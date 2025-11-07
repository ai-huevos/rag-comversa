"""
CEO Assumption Validation Framework
Validates CEO-prioritized macroprocesos against interview data
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import re


class CEOAssumptionValidator:
    """
    Validates CEO assumptions against interview data
    
    Compares CEO-prioritized macroprocesos from RECALIBRACIÓN FASE 1
    against actual pain points and automation opportunities found in interviews.
    """
    
    def __init__(self, db, ceo_priorities_path: str = "config/ceo_priorities.json"):
        """
        Initialize validator
        
        Args:
            db: EnhancedIntelligenceDB instance
            ceo_priorities_path: Path to CEO priorities JSON file
        """
        self.db = db
        self.ceo_priorities = self._load_ceo_priorities(ceo_priorities_path)
        self.keywords_mapping = self.ceo_priorities.get("keywords_mapping", {})
    
    def _load_ceo_priorities(self, path: str) -> Dict:
        """Load CEO priorities from JSON file"""
        priorities_file = Path(path)
        if not priorities_file.exists():
            raise FileNotFoundError(f"CEO priorities file not found: {path}")
        
        with open(priorities_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_priorities(self) -> Dict:
        """
        Validate CEO priorities against interview data
        
        Returns:
            Dict with validation results:
            - confirmed_priorities: Priorities with high data support
            - weak_priorities: Priorities with low data support
            - overlooked_opportunities: High-frequency pain points not in CEO list
            - emergent_opportunities: New automation candidates
        """
        print("Validating CEO priorities against interview data...")
        print()
        
        # Get all priorities
        all_priorities = []
        for category in ["quick_wins", "strategic", "incremental"]:
            all_priorities.extend(self.ceo_priorities.get(category, []))
        
        # Calculate data support for each priority
        confirmed = []
        weak = []
        
        for priority in all_priorities:
            support_score = self.calculate_data_support(priority)
            priority["data_support_score"] = support_score
            priority["interview_mentions"] = support_score["mention_count"]
            priority["support_percentage"] = support_score["support_percentage"]
            
            if support_score["support_percentage"] >= 30:
                confirmed.append(priority)
            else:
                weak.append(priority)
        
        # Find overlooked opportunities
        overlooked = self._find_overlooked_opportunities(all_priorities)
        
        # Find emergent opportunities
        emergent = self._find_emergent_opportunities(all_priorities)
        
        return {
            "confirmed_priorities": sorted(confirmed, key=lambda x: x["support_percentage"], reverse=True),
            "weak_priorities": sorted(weak, key=lambda x: x["support_percentage"]),
            "overlooked_opportunities": sorted(overlooked, key=lambda x: x["frequency"], reverse=True),
            "emergent_opportunities": sorted(emergent, key=lambda x: x.get("estimated_roi_months", 999)),
            "summary": {
                "total_priorities": len(all_priorities),
                "confirmed": len(confirmed),
                "weak": len(weak),
                "overlooked": len(overlooked),
                "emergent": len(emergent)
            }
        }
    
    def calculate_data_support(self, priority: Dict) -> Dict:
        """
        Calculate data support score for a CEO priority
        
        Score = (interviews mentioning this priority / total interviews)
        
        Args:
            priority: CEO priority dict with name and keywords
            
        Returns:
            Dict with mention_count, total_interviews, support_percentage
        """
        priority_name = priority["name"]
        keywords = self.keywords_mapping.get(priority_name, [])
        
        if not keywords:
            # Fallback: use words from priority name
            keywords = [word.lower() for word in priority_name.split() if len(word) > 3]
        
        # Get all interviews
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM interviews")
        total_interviews = cursor.fetchone()[0]
        
        if total_interviews == 0:
            return {
                "mention_count": 0,
                "total_interviews": 0,
                "support_percentage": 0.0,
                "matching_entities": []
            }
        
        # Search for mentions in pain points, processes, and automation candidates
        matching_entities = []
        
        # Search pain points
        cursor.execute("SELECT id, description, company FROM pain_points")
        for row in cursor.fetchall():
            pain_id, description, company = row
            if self._matches_keywords(description, keywords):
                matching_entities.append({
                    "type": "pain_point",
                    "id": pain_id,
                    "description": description,
                    "company": company
                })
        
        # Search processes
        cursor.execute("SELECT id, name, description, company FROM processes")
        for row in cursor.fetchall():
            proc_id, name, description, company = row
            text = f"{name} {description or ''}"
            if self._matches_keywords(text, keywords):
                matching_entities.append({
                    "type": "process",
                    "id": proc_id,
                    "name": name,
                    "company": company
                })
        
        # Search automation candidates
        cursor.execute("SELECT id, name, process, company FROM automation_candidates")
        for row in cursor.fetchall():
            auto_id, name, process, company = row
            text = f"{name} {process or ''}"
            if self._matches_keywords(text, keywords):
                matching_entities.append({
                    "type": "automation_candidate",
                    "id": auto_id,
                    "name": name,
                    "company": company
                })
        
        # Count unique interviews that mention this priority
        unique_interview_ids = set()
        for entity in matching_entities:
            # Get interview_id for this entity
            entity_type = entity["type"]
            entity_id = entity["id"]
            
            if entity_type == "pain_point":
                cursor.execute("SELECT interview_id FROM pain_points WHERE id = ?", (entity_id,))
            elif entity_type == "process":
                cursor.execute("SELECT interview_id FROM processes WHERE id = ?", (entity_id,))
            elif entity_type == "automation_candidate":
                cursor.execute("SELECT interview_id FROM automation_candidates WHERE id = ?", (entity_id,))
            
            result = cursor.fetchone()
            if result:
                unique_interview_ids.add(result[0])
        
        mention_count = len(unique_interview_ids)
        support_percentage = (mention_count / total_interviews) * 100 if total_interviews > 0 else 0
        
        return {
            "mention_count": mention_count,
            "total_interviews": total_interviews,
            "support_percentage": round(support_percentage, 1),
            "matching_entities": matching_entities[:10]  # Limit to 10 examples
        }
    
    def _matches_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text matches any of the keywords"""
        if not text:
            return False
        
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def _find_overlooked_opportunities(self, ceo_priorities: List[Dict]) -> List[Dict]:
        """
        Find high-frequency pain points NOT in CEO priorities
        
        Returns:
            List of overlooked opportunities
        """
        cursor = self.db.conn.cursor()
        
        # Get total interview count
        cursor.execute("SELECT COUNT(*) FROM interviews")
        total_interviews = cursor.fetchone()[0]
        
        if total_interviews == 0:
            return []
        
        # Get all pain points with their frequencies
        cursor.execute("""
            SELECT 
                description,
                type,
                COUNT(DISTINCT interview_id) as mention_count,
                GROUP_CONCAT(DISTINCT company) as companies,
                AVG(intensity_score) as avg_intensity,
                frequency
            FROM pain_points
            WHERE description IS NOT NULL AND description != ''
            GROUP BY description
            HAVING mention_count >= ?
            ORDER BY mention_count DESC
        """, (int(total_interviews * 0.3),))  # 30% threshold
        
        overlooked = []
        ceo_keywords_all = []
        for priority in ceo_priorities:
            ceo_keywords_all.extend(self.keywords_mapping.get(priority["name"], []))
        
        for row in cursor.fetchall():
            description, pain_type, mention_count, companies, avg_intensity, frequency = row
            
            # Check if this pain point matches any CEO priority
            if not self._matches_keywords(description, ceo_keywords_all):
                support_percentage = (mention_count / total_interviews) * 100
                
                overlooked.append({
                    "description": description,
                    "type": pain_type,
                    "mention_count": mention_count,
                    "support_percentage": round(support_percentage, 1),
                    "companies": companies.split(",") if companies else [],
                    "avg_intensity": round(avg_intensity, 1) if avg_intensity else None,
                    "frequency": frequency,
                    "overlooked_opportunity": True
                })
        
        return overlooked
    
    def _find_emergent_opportunities(self, ceo_priorities: List[Dict]) -> List[Dict]:
        """
        Find automation candidates that don't map to CEO priorities
        
        Returns:
            List of emergent opportunities
        """
        cursor = self.db.conn.cursor()
        
        # Get all automation candidates
        cursor.execute("""
            SELECT 
                id, name, process, impact, complexity,
                effort_score, impact_score, priority_quadrant,
                estimated_roi_months, estimated_annual_savings_usd,
                company
            FROM automation_candidates
        """)
        
        emergent = []
        ceo_keywords_all = []
        for priority in ceo_priorities:
            ceo_keywords_all.extend(self.keywords_mapping.get(priority["name"], []))
        
        for row in cursor.fetchall():
            (auto_id, name, process, impact, complexity, effort_score, 
             impact_score, priority_quadrant, roi_months, annual_savings, company) = row
            
            text = f"{name} {process or ''}"
            
            # Check if this automation matches any CEO priority
            if not self._matches_keywords(text, ceo_keywords_all):
                emergent.append({
                    "id": auto_id,
                    "name": name,
                    "process": process,
                    "impact": impact,
                    "complexity": complexity,
                    "effort_score": effort_score,
                    "impact_score": impact_score,
                    "priority_quadrant": priority_quadrant,
                    "estimated_roi_months": roi_months,
                    "estimated_annual_savings_usd": annual_savings,
                    "company": company,
                    "emergent_opportunity": True
                })
        
        return emergent
    
    def generate_validation_report(self, output_path: str = "ceo_validation_report.json") -> str:
        """
        Generate comprehensive validation report
        
        Args:
            output_path: Path to save report
            
        Returns:
            Path to generated report
        """
        validation_results = self.validate_priorities()
        
        # Add metadata
        report = {
            "metadata": {
                "generated_at": self.db.conn.execute("SELECT datetime('now')").fetchone()[0],
                "ceo_priorities_source": self.ceo_priorities.get("metadata", {}),
                "total_interviews": validation_results["summary"]["total_priorities"]
            },
            "validation_results": validation_results
        }
        
        # Save to file
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Validation report saved to: {output_path}")
        return str(output_file)
    
    def print_summary(self):
        """Print a human-readable summary of validation results"""
        results = self.validate_priorities()
        summary = results["summary"]
        
        print("=" * 70)
        print("CEO ASSUMPTION VALIDATION SUMMARY")
        print("=" * 70)
        print()
        
        print(f"Total CEO Priorities: {summary['total_priorities']}")
        print(f"  ✅ Confirmed (≥30% support): {summary['confirmed']}")
        print(f"  ⚠️  Weak (<30% support): {summary['weak']}")
        print()
        
        print(f"Data-Driven Discoveries:")
        print(f"  🔍 Overlooked Opportunities: {summary['overlooked']}")
        print(f"  💡 Emergent Opportunities: {summary['emergent']}")
        print()
        
        # Show top confirmed priorities
        if results["confirmed_priorities"]:
            print("Top Confirmed Priorities:")
            for i, priority in enumerate(results["confirmed_priorities"][:3], 1):
                print(f"  {i}. {priority['name']}")
                print(f"     Support: {priority['support_percentage']}% ({priority['interview_mentions']} interviews)")
        
        print()
        
        # Show weak priorities
        if results["weak_priorities"]:
            print("Weak Priorities (Need Validation):")
            for i, priority in enumerate(results["weak_priorities"][:3], 1):
                print(f"  {i}. {priority['name']}")
                print(f"     Support: {priority['support_percentage']}% ({priority['interview_mentions']} interviews)")
        
        print()
        
        # Show top overlooked opportunities
        if results["overlooked_opportunities"]:
            print("Top Overlooked Opportunities:")
            for i, opp in enumerate(results["overlooked_opportunities"][:3], 1):
                print(f"  {i}. {opp['description'][:60]}...")
                print(f"     Mentioned in: {opp['support_percentage']}% of interviews")
        
        print()
        print("=" * 70)
