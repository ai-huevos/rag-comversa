"""
Cross-Company Pattern Recognition
Identifies patterns, shared challenges, and standardization opportunities across companies
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from difflib import SequenceMatcher


class CrossCompanyAnalyzer:
    """
    Analyzes patterns across multiple companies
    
    Identifies:
    - Common pain points across companies
    - Standardization opportunities
    - Shared vs divergent approaches
    - Economies of scale opportunities
    """
    
    def __init__(self, db):
        """
        Initialize analyzer
        
        Args:
            db: EnhancedIntelligenceDB instance
        """
        self.db = db
        self.companies = self._get_companies()
    
    def _get_companies(self) -> List[str]:
        """Get list of all companies in database"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT DISTINCT company FROM interviews WHERE company IS NOT NULL")
        return [row[0] for row in cursor.fetchall()]
    
    def analyze_patterns(self) -> Dict:
        """
        Analyze cross-company patterns
        
        Returns:
            Dict with:
            - common_pain_points: Pain points shared across companies
            - standardization_opportunities: Processes that could be standardized
            - shared_systems: Systems used by multiple companies
            - divergent_approaches: Same process, different implementations
            - summary: Statistics
        """
        print("Analyzing cross-company patterns...")
        print(f"Companies: {', '.join(self.companies)}")
        print()
        
        # Detect common pain points
        common_pain_points = self._detect_common_pain_points()
        
        # Detect standardization opportunities
        standardization_opps = self._detect_standardization_opportunities()
        
        # Analyze shared systems
        shared_systems = self._analyze_shared_systems()
        
        # Detect divergent approaches
        divergent_approaches = self._detect_divergent_approaches()
        
        return {
            "common_pain_points": common_pain_points,
            "standardization_opportunities": standardization_opps,
            "shared_systems": shared_systems,
            "divergent_approaches": divergent_approaches,
            "summary": {
                "total_companies": len(self.companies),
                "common_pain_points": len(common_pain_points),
                "standardization_opportunities": len(standardization_opps),
                "shared_systems": len(shared_systems),
                "divergent_approaches": len(divergent_approaches)
            }
        }
    
    def _detect_common_pain_points(self) -> List[Dict]:
        """
        Detect pain points that appear across multiple companies
        
        Returns:
            List of common pain points with prevalence scores
        """
        cursor = self.db.conn.cursor()
        
        # Get all pain points grouped by similarity
        cursor.execute("""
            SELECT 
                description,
                type,
                company,
                COUNT(*) as mention_count,
                AVG(intensity_score) as avg_intensity
            FROM pain_points
            WHERE description IS NOT NULL AND description != ''
            GROUP BY description, company
        """)
        
        # Group similar pain points
        pain_point_groups = defaultdict(lambda: {"companies": set(), "descriptions": [], "total_mentions": 0, "avg_intensity": []})
        
        rows = cursor.fetchall()
        for description, pain_type, company, mention_count, avg_intensity in rows:
            # Find similar pain points using semantic similarity
            group_key = self._find_similar_group(description, pain_point_groups.keys())
            
            if group_key is None:
                group_key = description
            
            pain_point_groups[group_key]["companies"].add(company)
            pain_point_groups[group_key]["descriptions"].append(description)
            pain_point_groups[group_key]["total_mentions"] += mention_count
            if avg_intensity:
                pain_point_groups[group_key]["avg_intensity"].append(avg_intensity)
            pain_point_groups[group_key]["type"] = pain_type
        
        # Filter for pain points in multiple companies
        common_pain_points = []
        for description, data in pain_point_groups.items():
            if len(data["companies"]) >= 2:  # At least 2 companies
                prevalence = len(data["companies"]) / len(self.companies)
                
                common_pain_points.append({
                    "description": description,
                    "type": data.get("type", "Unknown"),
                    "companies_affected": sorted(list(data["companies"])),
                    "prevalence": round(prevalence, 2),
                    "total_mentions": data["total_mentions"],
                    "avg_intensity": round(sum(data["avg_intensity"]) / len(data["avg_intensity"]), 1) if data["avg_intensity"] else None,
                    "shared_challenge": True
                })
        
        # Sort by prevalence and mentions
        common_pain_points.sort(key=lambda x: (x["prevalence"], x["total_mentions"]), reverse=True)
        
        return common_pain_points
    
    def _find_similar_group(self, description: str, existing_groups: List[str], threshold: float = 0.7) -> Optional[str]:
        """
        Find if description is similar to any existing group
        
        Args:
            description: Pain point description
            existing_groups: List of existing group keys
            threshold: Similarity threshold (0-1)
            
        Returns:
            Group key if similar group found, None otherwise
        """
        description_lower = description.lower()
        
        for group_key in existing_groups:
            group_key_lower = group_key.lower()
            
            # Calculate similarity
            similarity = SequenceMatcher(None, description_lower, group_key_lower).ratio()
            
            if similarity >= threshold:
                return group_key
            
            # Also check for key word overlap
            desc_words = set(description_lower.split())
            group_words = set(group_key_lower.split())
            
            # Remove common words
            common_words = {"el", "la", "los", "las", "de", "del", "en", "es", "y", "a", "con", "por", "para", "que", "un", "una"}
            desc_words -= common_words
            group_words -= common_words
            
            if len(desc_words) > 0 and len(group_words) > 0:
                overlap = len(desc_words & group_words) / min(len(desc_words), len(group_words))
                if overlap >= 0.6:  # 60% word overlap
                    return group_key
        
        return None
    
    def _detect_standardization_opportunities(self) -> List[Dict]:
        """
        Detect processes that exist in multiple companies with different implementations
        
        Returns:
            List of standardization opportunities
        """
        cursor = self.db.conn.cursor()
        
        # Get all processes grouped by name
        cursor.execute("""
            SELECT 
                name,
                company,
                description,
                systems,
                frequency
            FROM processes
            WHERE name IS NOT NULL AND name != ''
        """)
        
        # Group processes by similar names
        process_groups = defaultdict(lambda: {"companies": {}, "implementations": []})
        
        for name, company, description, systems, frequency in cursor.fetchall():
            # Find similar process group
            group_key = self._find_similar_group(name, process_groups.keys(), threshold=0.6)
            
            if group_key is None:
                group_key = name
            
            process_groups[group_key]["companies"][company] = {
                "description": description,
                "systems": systems,
                "frequency": frequency
            }
            process_groups[group_key]["implementations"].append({
                "company": company,
                "description": description,
                "systems": systems
            })
        
        # Find processes in multiple companies with different implementations
        standardization_opps = []
        
        for process_name, data in process_groups.items():
            if len(data["companies"]) >= 2:  # At least 2 companies
                # Check if implementations differ
                implementations = data["implementations"]
                systems_used = [impl.get("systems", "") for impl in implementations]
                
                # If systems differ significantly, it's a standardization opportunity
                unique_systems = set(systems_used)
                if len(unique_systems) > 1:
                    standardization_opps.append({
                        "process_name": process_name,
                        "companies_affected": sorted(list(data["companies"].keys())),
                        "implementations": implementations,
                        "standardization_opportunity": True,
                        "potential_benefit": "Shared solution, reduced costs, consistent processes"
                    })
        
        return standardization_opps
    
    def _analyze_shared_systems(self) -> List[Dict]:
        """
        Analyze systems used by multiple companies
        
        Returns:
            List of shared systems with pain points by company
        """
        cursor = self.db.conn.cursor()
        
        # Get systems used by multiple companies
        cursor.execute("""
            SELECT 
                name,
                companies_using,
                pain_points,
                integration_pain_points,
                user_satisfaction_score
            FROM systems
            WHERE companies_using IS NOT NULL
        """)
        
        shared_systems = []
        
        for name, companies_json, pain_points_json, integration_pain_json, satisfaction in cursor.fetchall():
            if not companies_json:
                continue
            
            companies = json.loads(companies_json) if companies_json else []
            
            if len(companies) >= 2:  # Shared by at least 2 companies
                pain_points = json.loads(pain_points_json) if pain_points_json else []
                integration_pain = json.loads(integration_pain_json) if integration_pain_json else []
                
                shared_systems.append({
                    "system_name": name,
                    "companies_using": companies,
                    "usage_count": len(companies),
                    "pain_points": pain_points,
                    "integration_pain_points": integration_pain,
                    "user_satisfaction_score": satisfaction,
                    "shared_solution_opportunity": len(pain_points) > 0 or len(integration_pain) > 0
                })
        
        # Sort by usage count
        shared_systems.sort(key=lambda x: x["usage_count"], reverse=True)
        
        return shared_systems
    
    def _detect_divergent_approaches(self) -> List[Dict]:
        """
        Detect same process with significantly different approaches
        
        Returns:
            List of divergent approaches
        """
        cursor = self.db.conn.cursor()
        
        # Get automation candidates grouped by process
        cursor.execute("""
            SELECT 
                process,
                company,
                name,
                complexity,
                systems_involved
            FROM automation_candidates
            WHERE process IS NOT NULL AND process != ''
        """)
        
        # Group by similar process names
        process_groups = defaultdict(lambda: {"companies": {}, "approaches": []})
        
        for process, company, name, complexity, systems in cursor.fetchall():
            group_key = self._find_similar_group(process, process_groups.keys(), threshold=0.6)
            
            if group_key is None:
                group_key = process
            
            process_groups[group_key]["companies"][company] = {
                "automation_name": name,
                "complexity": complexity,
                "systems": systems
            }
            process_groups[group_key]["approaches"].append({
                "company": company,
                "approach": name,
                "complexity": complexity
            })
        
        # Find processes with divergent approaches
        divergent = []
        
        for process_name, data in process_groups.items():
            if len(data["companies"]) >= 2:
                # Check if approaches differ
                approaches = [a["approach"] for a in data["approaches"]]
                unique_approaches = set(approaches)
                
                if len(unique_approaches) > 1:
                    divergent.append({
                        "process": process_name,
                        "companies": sorted(list(data["companies"].keys())),
                        "approaches": data["approaches"],
                        "divergent_approach": True,
                        "recommendation": "Evaluate best approach and standardize"
                    })
        
        return divergent
    
    def generate_insights_report(self, output_path: str = "cross_company_insights.json") -> str:
        """
        Generate comprehensive cross-company insights report
        
        Args:
            output_path: Path to save report
            
        Returns:
            Path to generated report
        """
        analysis_results = self.analyze_patterns()
        
        # Add metadata
        report = {
            "metadata": {
                "generated_at": self.db.conn.execute("SELECT datetime('now')").fetchone()[0],
                "companies_analyzed": self.companies,
                "total_companies": len(self.companies)
            },
            "analysis_results": analysis_results,
            "recommendations": self._generate_recommendations(analysis_results)
        }
        
        # Save to file
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Cross-company insights report saved to: {output_path}")
        return str(output_file)
    
    def _generate_recommendations(self, analysis: Dict) -> List[Dict]:
        """Generate actionable recommendations from analysis"""
        recommendations = []
        
        # Recommend shared solutions for common pain points
        for pain_point in analysis["common_pain_points"][:5]:  # Top 5
            if pain_point["prevalence"] >= 0.67:  # 2/3 or more companies
                recommendations.append({
                    "type": "shared_solution",
                    "priority": "high",
                    "description": f"Develop shared solution for: {pain_point['description'][:60]}...",
                    "affected_companies": pain_point["companies_affected"],
                    "potential_impact": "High - affects multiple companies",
                    "economies_of_scale": True
                })
        
        # Recommend standardization
        for opp in analysis["standardization_opportunities"][:3]:  # Top 3
            recommendations.append({
                "type": "standardization",
                "priority": "medium",
                "description": f"Standardize process: {opp['process_name']}",
                "affected_companies": opp["companies_affected"],
                "potential_impact": "Medium - reduce complexity, improve consistency",
                "economies_of_scale": True
            })
        
        # Recommend shared system improvements
        for system in analysis["shared_systems"][:3]:  # Top 3
            if system.get("shared_solution_opportunity"):
                recommendations.append({
                    "type": "shared_system_improvement",
                    "priority": "medium",
                    "description": f"Improve shared system: {system['system_name']}",
                    "affected_companies": system["companies_using"],
                    "potential_impact": "Medium - benefits all users",
                    "economies_of_scale": True
                })
        
        return recommendations
    
    def print_summary(self):
        """Print human-readable summary of cross-company analysis"""
        results = self.analyze_patterns()
        summary = results["summary"]
        
        print("=" * 70)
        print("CROSS-COMPANY PATTERN ANALYSIS")
        print("=" * 70)
        print()
        
        print(f"Companies Analyzed: {summary['total_companies']}")
        print(f"  {', '.join(self.companies)}")
        print()
        
        print(f"Patterns Identified:")
        print(f"  🔗 Common Pain Points: {summary['common_pain_points']}")
        print(f"  📊 Standardization Opportunities: {summary['standardization_opportunities']}")
        print(f"  💻 Shared Systems: {summary['shared_systems']}")
        print(f"  🔀 Divergent Approaches: {summary['divergent_approaches']}")
        print()
        
        # Show top common pain points
        if results["common_pain_points"]:
            print("Top Shared Challenges:")
            for i, pain in enumerate(results["common_pain_points"][:3], 1):
                print(f"  {i}. {pain['description'][:60]}...")
                print(f"     Companies: {', '.join(pain['companies_affected'])}")
                print(f"     Prevalence: {int(pain['prevalence'] * 100)}%")
        
        print()
        
        # Show standardization opportunities
        if results["standardization_opportunities"]:
            print("Standardization Opportunities:")
            for i, opp in enumerate(results["standardization_opportunities"][:3], 1):
                print(f"  {i}. {opp['process_name']}")
                print(f"     Companies: {', '.join(opp['companies_affected'])}")
        
        print()
        
        # Show shared systems
        if results["shared_systems"]:
            print("Shared Systems:")
            for i, system in enumerate(results["shared_systems"][:3], 1):
                print(f"  {i}. {system['system_name']}")
                print(f"     Used by: {', '.join(system['companies_using'])}")
        
        print()
        print("=" * 70)
