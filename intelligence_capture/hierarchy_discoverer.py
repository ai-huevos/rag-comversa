"""
Dynamic Hierarchy Discovery System
Discovers actual organizational hierarchy from interview data and validates against predefined structure
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from openai import OpenAI
import os


class HierarchyDiscoverer:
    """
    Discovers organizational hierarchy from interviews
    
    Extracts what people actually say about their organizational structure
    and compares it against predefined hierarchy to find:
    - Naming inconsistencies
    - New organizational units
    - Missing expected units
    - Reporting relationships
    """
    
    def __init__(self, db, predefined_hierarchy_path: str = "config/companies.json", openai_api_key: Optional[str] = None):
        """
        Initialize hierarchy discoverer
        
        Args:
            db: EnhancedIntelligenceDB instance
            predefined_hierarchy_path: Path to predefined hierarchy JSON
            openai_api_key: OpenAI API key for LLM extraction
        """
        self.db = db
        self.predefined_hierarchy = self._load_predefined_hierarchy(predefined_hierarchy_path)
        
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def _load_predefined_hierarchy(self, path: str) -> Dict:
        """Load predefined organizational hierarchy"""
        hierarchy_file = Path(path)
        if not hierarchy_file.exists():
            print(f"Warning: Predefined hierarchy file not found: {path}")
            return {"companies": []}
        
        with open(hierarchy_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def discover_hierarchy(self) -> Dict:
        """
        Discover organizational hierarchy from all interviews
        
        Returns:
            Dict with discovered hierarchy and validation results
        """
        print("Discovering organizational hierarchy from interviews...")
        print()
        
        # Extract org structure from each interview
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, company, respondent, role, raw_data, discovered_org_structure
            FROM interviews
        """)
        
        discoveries = []
        for interview_id, company, respondent, role, raw_data_json, discovered_json in cursor.fetchall():
            # Check if already extracted
            if discovered_json:
                discovered = json.loads(discovered_json)
            else:
                # Extract org structure from interview
                raw_data = json.loads(raw_data_json) if raw_data_json else {}
                qa_pairs = raw_data.get("qa_pairs", {})
                
                discovered = self.extract_org_structure(qa_pairs, company, role)
                
                # Store in database
                cursor.execute("""
                    UPDATE interviews
                    SET discovered_org_structure = ?,
                        org_structure_confidence = ?
                    WHERE id = ?
                """, (
                    json.dumps(discovered),
                    discovered.get("confidence", 0.5),
                    interview_id
                ))
            
            discoveries.append({
                "interview_id": interview_id,
                "company": company,
                "respondent": respondent,
                "role": role,
                "discovered": discovered
            })
        
        self.db.conn.commit()
        
        # Aggregate discoveries
        aggregated = self._aggregate_discoveries(discoveries)
        
        # Validate against predefined
        validation = self._validate_against_predefined(aggregated)
        
        return {
            "discoveries": discoveries,
            "aggregated": aggregated,
            "validation": validation
        }
    
    def extract_org_structure(self, qa_pairs: Dict, company: str, role: str) -> Dict:
        """
        Extract organizational structure from interview Q&A
        
        Args:
            qa_pairs: Interview questions and answers
            company: Company name
            role: Respondent role
            
        Returns:
            Dict with discovered org structure
        """
        if not self.client:
            # Fallback: basic extraction without LLM
            return {
                "self_identified_company": company,
                "self_identified_business_unit": None,
                "self_identified_department": None,
                "reports_to_role": None,
                "reports_to_department": None,
                "coordinates_with": [],
                "confidence": 0.3,
                "extraction_reasoning": "No LLM available, using basic extraction"
            }
        
        # Combine Q&A into text
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        prompt = f"""You are analyzing an interview to extract organizational structure information. Focus on what the person actually says about their organization.

**Interview Context:**
- Company: {company}
- Role: {role}

**Interview Text:**
{full_text[:3000]}

**Your Task:**
Extract organizational structure information from what the person says. Look for:

1. **self_identified_company**: What company do they say they work for? (exact words)
2. **self_identified_business_unit**: What business unit/division do they mention? (exact words they use, e.g., "Alimentos y Bebidas", "F&B", "Hospedaje")
3. **self_identified_department**: What department/team are they in? (exact words, e.g., "Restaurantes", "Cocina", "Recepción")
4. **reports_to_role**: Who do they report to? (role/title, e.g., "Gerente de A&B", "Director")
5. **reports_to_department**: What department does their boss belong to?
6. **coordinates_with**: What other departments/teams do they coordinate with? (list)
7. **other_units_mentioned**: Any other organizational units mentioned? (list)

**Important:**
- Use EXACT words they use, not standardized terms
- If they say "A&B" don't change it to "Food & Beverage"
- If they say "Cocina" don't change it to "Kitchen"
- Capture naming variations (this helps us find inconsistencies)
- If something isn't mentioned, use null

**Return Format:**
{{
  "self_identified_company": "exact company name they use",
  "self_identified_business_unit": "exact business unit name or null",
  "self_identified_department": "exact department name or null",
  "reports_to_role": "role title or null",
  "reports_to_department": "department name or null",
  "coordinates_with": ["dept1", "dept2"],
  "other_units_mentioned": ["unit1", "unit2"],
  "confidence": 0.0-1.0,
  "extraction_reasoning": "brief explanation"
}}
"""
        
        try:
            from intelligence_capture.extractors import call_llm_with_fallback
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert in organizational analysis. You extract organizational structure information exactly as people describe it, preserving their terminology. Always return valid JSON."
                },
                {"role": "user", "content": prompt}
            ]
            
            response_content = call_llm_with_fallback(self.client, messages, temperature=0.1)
            
            if not response_content:
                return {
                    "self_identified_company": company,
                    "confidence": 0.3,
                    "extraction_reasoning": "LLM extraction failed"
                }
            
            result = json.loads(response_content)
            
            # Ensure required fields
            result.setdefault("self_identified_company", company)
            result.setdefault("self_identified_business_unit", None)
            result.setdefault("self_identified_department", None)
            result.setdefault("reports_to_role", None)
            result.setdefault("reports_to_department", None)
            result.setdefault("coordinates_with", [])
            result.setdefault("other_units_mentioned", [])
            result.setdefault("confidence", 0.7)
            result.setdefault("extraction_reasoning", "Extracted by LLM")
            
            return result
            
        except Exception as e:
            print(f"Warning: Org structure extraction failed: {e}")
            return {
                "self_identified_company": company,
                "confidence": 0.3,
                "extraction_reasoning": f"Extraction error: {str(e)[:100]}"
            }
    
    def _aggregate_discoveries(self, discoveries: List[Dict]) -> Dict:
        """
        Aggregate organizational discoveries across all interviews
        
        Returns:
            Dict with aggregated org structure by company
        """
        aggregated = defaultdict(lambda: {
            "business_units": defaultdict(lambda: {"count": 0, "names": set(), "departments": defaultdict(lambda: {"count": 0, "names": set()})}),
            "departments": defaultdict(lambda: {"count": 0, "names": set()}),
            "reporting_relationships": [],
            "coordination_patterns": defaultdict(int)
        })
        
        for discovery in discoveries:
            company = discovery["company"]
            discovered = discovery["discovered"]
            
            # Aggregate business units
            bu = discovered.get("self_identified_business_unit")
            if bu:
                aggregated[company]["business_units"][bu.lower()]["count"] += 1
                aggregated[company]["business_units"][bu.lower()]["names"].add(bu)
            
            # Aggregate departments
            dept = discovered.get("self_identified_department")
            if dept:
                aggregated[company]["departments"][dept.lower()]["count"] += 1
                aggregated[company]["departments"][dept.lower()]["names"].add(dept)
                
                # Link department to business unit
                if bu:
                    aggregated[company]["business_units"][bu.lower()]["departments"][dept.lower()]["count"] += 1
                    aggregated[company]["business_units"][bu.lower()]["departments"][dept.lower()]["names"].add(dept)
            
            # Aggregate reporting relationships
            if discovered.get("reports_to_role"):
                aggregated[company]["reporting_relationships"].append({
                    "from_role": discovery["role"],
                    "to_role": discovered["reports_to_role"],
                    "to_department": discovered.get("reports_to_department")
                })
            
            # Aggregate coordination patterns
            for coord_dept in discovered.get("coordinates_with", []):
                if coord_dept:
                    aggregated[company]["coordination_patterns"][coord_dept.lower()] += 1
        
        # Convert sets to lists for JSON serialization
        result = {}
        for company, data in aggregated.items():
            result[company] = {
                "business_units": {
                    bu: {
                        "count": info["count"],
                        "names": list(info["names"]),
                        "most_common": list(info["names"])[0] if info["names"] else None,  # Just take first name
                        "departments": {
                            dept: {
                                "count": dept_info["count"],
                                "names": list(dept_info["names"]),
                                "most_common": list(dept_info["names"])[0] if dept_info["names"] else None
                            }
                            for dept, dept_info in info["departments"].items()
                        }
                    }
                    for bu, info in data["business_units"].items()
                },
                "departments": {
                    dept: {
                        "count": info["count"],
                        "names": list(info["names"]),
                        "most_common": list(info["names"])[0] if info["names"] else None
                    }
                    for dept, info in data["departments"].items()
                },
                "reporting_relationships": data["reporting_relationships"],
                "coordination_patterns": dict(data["coordination_patterns"])
            }
        
        return result
    
    def _validate_against_predefined(self, aggregated: Dict) -> Dict:
        """
        Validate discovered hierarchy against predefined hierarchy
        
        Returns:
            Dict with validation results
        """
        validation = {
            "confirmed_structure": [],
            "naming_inconsistencies": [],
            "new_discoveries": [],
            "missing_expected": [],
            "summary": {
                "total_companies": len(aggregated),
                "confirmed": 0,
                "inconsistencies": 0,
                "new_discoveries": 0,
                "missing": 0
            }
        }
        
        # Get predefined companies
        predefined_companies = {c["name"]: c for c in self.predefined_hierarchy.get("companies", [])}
        
        for company_name, discovered_data in aggregated.items():
            if company_name not in predefined_companies:
                validation["new_discoveries"].append({
                    "type": "company",
                    "name": company_name,
                    "evidence": f"Found in {len(discovered_data.get('business_units', {}))} interviews"
                })
                continue
            
            predefined = predefined_companies[company_name]
            # Handle both list of strings and list of dicts
            predefined_bus_raw = predefined.get("business_units", [])
            if predefined_bus_raw and isinstance(predefined_bus_raw[0], dict):
                predefined_bus = set(bu.get("name", bu) for bu in predefined_bus_raw)
            else:
                predefined_bus = set(predefined_bus_raw)
            
            # Check business units
            for bu_key, bu_data in discovered_data.get("business_units", {}).items():
                discovered_names = bu_data["names"]
                most_common = bu_data["most_common"]
                count = bu_data["count"]
                
                # Check if matches any predefined BU
                matched = False
                for pred_bu in predefined_bus:
                    if bu_key in pred_bu.lower() or pred_bu.lower() in bu_key:
                        # Found match
                        if most_common != pred_bu:
                            # Naming inconsistency
                            validation["naming_inconsistencies"].append({
                                "type": "business_unit",
                                "company": company_name,
                                "predefined": pred_bu,
                                "discovered": most_common,
                                "count": count,
                                "recommendation": f"Update to '{most_common}' or add as alias"
                            })
                            validation["summary"]["inconsistencies"] += 1
                        else:
                            # Confirmed
                            validation["confirmed_structure"].append({
                                "type": "business_unit",
                                "company": company_name,
                                "name": most_common,
                                "count": count
                            })
                            validation["summary"]["confirmed"] += 1
                        matched = True
                        break
                
                if not matched:
                    # New discovery
                    validation["new_discoveries"].append({
                        "type": "business_unit",
                        "company": company_name,
                        "name": most_common,
                        "count": count,
                        "recommendation": f"Add '{most_common}' to {company_name} business units"
                    })
                    validation["summary"]["new_discoveries"] += 1
            
            # Check for missing expected BUs
            discovered_bu_keys = set(discovered_data.get("business_units", {}).keys())
            for pred_bu in predefined_bus:
                if not any(pred_bu.lower() in bu_key or bu_key in pred_bu.lower() for bu_key in discovered_bu_keys):
                    validation["missing_expected"].append({
                        "type": "business_unit",
                        "company": company_name,
                        "name": pred_bu,
                        "recommendation": "Verify if this BU exists or remove from predefined"
                    })
                    validation["summary"]["missing"] += 1
        
        return validation
    
    def generate_validation_report(self, output_path: str = "hierarchy_validation_report.json") -> str:
        """
        Generate comprehensive hierarchy validation report
        
        Args:
            output_path: Path to save report
            
        Returns:
            Path to generated report
        """
        hierarchy_data = self.discover_hierarchy()
        
        report = {
            "metadata": {
                "generated_at": self.db.conn.execute("SELECT datetime('now')").fetchone()[0],
                "total_interviews": len(hierarchy_data["discoveries"])
            },
            "aggregated_hierarchy": hierarchy_data["aggregated"],
            "validation_results": hierarchy_data["validation"],
            "recommended_actions": self._generate_recommended_actions(hierarchy_data["validation"])
        }
        
        # Save to file
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Hierarchy validation report saved to: {output_path}")
        return str(output_file)
    
    def _generate_recommended_actions(self, validation: Dict) -> List[Dict]:
        """Generate prioritized recommended actions"""
        actions = []
        
        # High priority: New discoveries with high evidence
        for discovery in validation["new_discoveries"]:
            if discovery.get("count", 0) >= 3:
                actions.append({
                    "priority": "high",
                    "action": discovery.get("recommendation", "Review discovery"),
                    "evidence": f"{discovery.get('count', 0)} interviews",
                    "type": discovery["type"],
                    "company": discovery.get("company", "N/A")
                })
        
        # Medium priority: Naming inconsistencies
        for inconsistency in validation["naming_inconsistencies"]:
            actions.append({
                "priority": "medium",
                "action": inconsistency.get("recommendation", "Review naming"),
                "evidence": f"{inconsistency.get('count', 0)} interviews",
                "type": inconsistency["type"],
                "company": inconsistency.get("company", "N/A")
            })
        
        # Low priority: Missing expected units
        for missing in validation["missing_expected"]:
            actions.append({
                "priority": "low",
                "action": missing.get("recommendation", "Verify existence"),
                "evidence": "Not found in interviews",
                "type": missing["type"],
                "company": missing.get("company", "N/A")
            })
        
        return actions
    
    def print_summary(self):
        """Print human-readable summary of hierarchy discovery"""
        hierarchy_data = self.discover_hierarchy()
        validation = hierarchy_data["validation"]
        summary = validation["summary"]
        
        print("=" * 70)
        print("HIERARCHY DISCOVERY & VALIDATION SUMMARY")
        print("=" * 70)
        print()
        
        print(f"Total Companies: {summary['total_companies']}")
        print(f"Total Interviews Analyzed: {len(hierarchy_data['discoveries'])}")
        print()
        
        print(f"Validation Results:")
        print(f"  ✅ Confirmed Structure: {summary['confirmed']}")
        print(f"  ⚠️  Naming Inconsistencies: {summary['inconsistencies']}")
        print(f"  🆕 New Discoveries: {summary['new_discoveries']}")
        print(f"  ❓ Missing Expected: {summary['missing']}")
        print()
        
        # Show naming inconsistencies
        if validation["naming_inconsistencies"]:
            print("Naming Inconsistencies:")
            for inc in validation["naming_inconsistencies"][:3]:
                print(f"  - {inc['company']}: '{inc['predefined']}' vs '{inc['discovered']}'")
                print(f"    Evidence: {inc['count']} interviews")
        
        print()
        
        # Show new discoveries
        if validation["new_discoveries"]:
            print("New Discoveries:")
            for disc in validation["new_discoveries"][:3]:
                print(f"  - {disc.get('company', 'N/A')}: {disc['name']} ({disc['type']})")
                print(f"    Evidence: {disc.get('count', 0)} interviews")
        
        print()
        print("=" * 70)
