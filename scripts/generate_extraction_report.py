#!/usr/bin/env python
"""
Generate Comprehensive Extraction Report
Creates detailed analytics and visualizations from extracted data
"""
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.config import DB_PATH, REPORTS_DIR
from intelligence_capture.ceo_validator import CEOAssumptionValidator
from intelligence_capture.cross_company_analyzer import CrossCompanyAnalyzer
from intelligence_capture.hierarchy_discoverer import HierarchyDiscoverer


class ExtractionReportGenerator:
    """Generates comprehensive extraction report with analytics"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db = None
        self.report = {
            "metadata": {},
            "extraction_summary": {},
            "entity_statistics": {},
            "quality_metrics": {},
            "ceo_validation": {},
            "cross_company_insights": {},
            "hierarchy_validation": {},
            "top_findings": {}
        }
    
    def generate(self) -> Dict:
        """Generate complete extraction report"""
        print("=" * 70)
        print("📊 GENERATING COMPREHENSIVE EXTRACTION REPORT")
        print("=" * 70)
        
        # Connect to database
        self.db = EnhancedIntelligenceDB(self.db_path)
        self.db.connect()
        
        # Generate each section
        self._generate_metadata()
        self._generate_extraction_summary()
        self._generate_entity_statistics()
        self._generate_quality_metrics()
        self._generate_ceo_validation()
        self._generate_cross_company_insights()
        self._generate_hierarchy_validation()
        self._generate_top_findings()
        
        # Close database
        self.db.close()
        
        return self.report
    
    def _generate_metadata(self):
        """Generate report metadata"""
        print("\n📋 Generating metadata...")
        
        self.report["metadata"] = {
            "report_generated_at": datetime.now().isoformat(),
            "database_path": str(self.db_path),
            "database_size_mb": self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        }
    
    def _generate_extraction_summary(self):
        """Generate extraction summary statistics"""
        print("📊 Generating extraction summary...")
        
        cursor = self.db.conn.cursor()
        
        # Count interviews
        cursor.execute("SELECT COUNT(*) FROM interviews")
        total_interviews = cursor.fetchone()[0]
        
        # Count by company
        cursor.execute("""
            SELECT company, COUNT(*) 
            FROM interviews 
            GROUP BY company
        """)
        by_company = dict(cursor.fetchall())
        
        self.report["extraction_summary"] = {
            "total_interviews": total_interviews,
            "interviews_by_company": by_company
        }
    
    def _generate_entity_statistics(self):
        """Generate statistics for each entity type"""
        print("📈 Generating entity statistics...")
        
        cursor = self.db.conn.cursor()
        
        entity_tables = [
            "communication_channels",
            "decision_points",
            "data_flows",
            "temporal_patterns",
            "failure_modes",
            "pain_points",
            "systems",
            "automation_candidates",
            "team_structures",
            "knowledge_gaps",
            "success_patterns",
            "budget_constraints",
            "external_dependencies"
        ]
        
        stats = {}
        
        for table in entity_tables:
            try:
                # Total count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                total = cursor.fetchone()[0]
                
                # By company
                cursor.execute(f"""
                    SELECT company_name, COUNT(*) 
                    FROM {table} 
                    WHERE company_name IS NOT NULL
                    GROUP BY company_name
                """)
                by_company = dict(cursor.fetchall())
                
                # Average confidence score
                cursor.execute(f"""
                    SELECT AVG(confidence_score) 
                    FROM {table}
                    WHERE confidence_score IS NOT NULL
                """)
                avg_confidence = cursor.fetchone()[0] or 0
                
                # Needs review count
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM {table}
                    WHERE needs_review = 1
                """)
                needs_review = cursor.fetchone()[0]
                
                stats[table] = {
                    "total": total,
                    "by_company": by_company,
                    "avg_confidence_score": round(avg_confidence, 3),
                    "needs_review": needs_review,
                    "review_percentage": round(needs_review / total * 100, 1) if total > 0 else 0
                }
                
            except Exception as e:
                print(f"  ⚠️  Error processing {table}: {str(e)}")
                stats[table] = {"error": str(e)}
        
        self.report["entity_statistics"] = stats
    
    def _generate_quality_metrics(self):
        """Generate data quality metrics"""
        print("🔍 Generating quality metrics...")
        
        cursor = self.db.conn.cursor()
        
        # Overall confidence distribution
        entity_tables = [
            "communication_channels", "decision_points", "data_flows",
            "temporal_patterns", "failure_modes", "pain_points",
            "automation_candidates", "team_structures", "knowledge_gaps",
            "success_patterns", "budget_constraints", "external_dependencies"
        ]
        
        confidence_distribution = {
            "high (>= 0.8)": 0,
            "medium (0.6-0.8)": 0,
            "low (< 0.6)": 0
        }
        
        total_entities = 0
        
        for table in entity_tables:
            try:
                cursor.execute(f"""
                    SELECT 
                        SUM(CASE WHEN confidence_score >= 0.8 THEN 1 ELSE 0 END) as high,
                        SUM(CASE WHEN confidence_score >= 0.6 AND confidence_score < 0.8 THEN 1 ELSE 0 END) as medium,
                        SUM(CASE WHEN confidence_score < 0.6 THEN 1 ELSE 0 END) as low,
                        COUNT(*) as total
                    FROM {table}
                    WHERE confidence_score IS NOT NULL
                """)
                
                result = cursor.fetchone()
                if result:
                    confidence_distribution["high (>= 0.8)"] += result[0] or 0
                    confidence_distribution["medium (0.6-0.8)"] += result[1] or 0
                    confidence_distribution["low (< 0.6)"] += result[2] or 0
                    total_entities += result[3] or 0
                    
            except Exception as e:
                print(f"  ⚠️  Error processing {table}: {str(e)}")
        
        self.report["quality_metrics"] = {
            "total_entities_with_confidence": total_entities,
            "confidence_distribution": confidence_distribution,
            "confidence_percentages": {
                k: round(v / total_entities * 100, 1) if total_entities > 0 else 0
                for k, v in confidence_distribution.items()
            }
        }
    
    def _generate_ceo_validation(self):
        """Generate CEO assumption validation results"""
        print("👔 Generating CEO validation...")
        
        try:
            validator = CEOAssumptionValidator(self.db)
            validation_report = validator.validate_priorities()
            
            self.report["ceo_validation"] = {
                "confirmed_priorities": len(validation_report.get("confirmed_priorities", [])),
                "weak_priorities": len(validation_report.get("weak_priorities", [])),
                "overlooked_opportunities": len(validation_report.get("overlooked_opportunities", [])),
                "details": validation_report
            }
            
        except Exception as e:
            print(f"  ⚠️  CEO validation error: {str(e)}")
            self.report["ceo_validation"] = {"error": str(e)}
    
    def _generate_cross_company_insights(self):
        """Generate cross-company pattern analysis"""
        print("🌐 Generating cross-company insights...")
        
        try:
            analyzer = CrossCompanyAnalyzer(self.db)
            insights = analyzer.analyze()
            
            self.report["cross_company_insights"] = {
                "common_pain_points": len(insights.get("common_pain_points", [])),
                "standardization_opportunities": len(insights.get("standardization_opportunities", [])),
                "details": insights
            }
            
        except Exception as e:
            print(f"  ⚠️  Cross-company analysis error: {str(e)}")
            self.report["cross_company_insights"] = {"error": str(e)}
    
    def _generate_hierarchy_validation(self):
        """Generate organizational hierarchy validation"""
        print("🏢 Generating hierarchy validation...")
        
        try:
            discoverer = HierarchyDiscoverer(self.db)
            hierarchy_report = discoverer.discover_and_validate()
            
            self.report["hierarchy_validation"] = {
                "confirmed_structure": len(hierarchy_report.get("confirmed_structure", [])),
                "naming_inconsistencies": len(hierarchy_report.get("naming_inconsistencies", [])),
                "new_discoveries": len(hierarchy_report.get("new_discoveries", [])),
                "details": hierarchy_report
            }
            
        except Exception as e:
            print(f"  ⚠️  Hierarchy validation error: {str(e)}")
            self.report["hierarchy_validation"] = {"error": str(e)}
    
    def _generate_top_findings(self):
        """Generate top findings and insights"""
        print("🔥 Generating top findings...")
        
        cursor = self.db.conn.cursor()
        
        findings = {}
        
        # Top pain points by intensity
        try:
            cursor.execute("""
                SELECT description, intensity_score, frequency, company_name
                FROM pain_points
                WHERE intensity_score IS NOT NULL
                ORDER BY intensity_score DESC, 
                         CASE frequency
                             WHEN 'Daily' THEN 1
                             WHEN 'Weekly' THEN 2
                             WHEN 'Monthly' THEN 3
                             ELSE 4
                         END
                LIMIT 10
            """)
            
            findings["top_pain_points"] = [
                {
                    "description": row[0],
                    "intensity": row[1],
                    "frequency": row[2],
                    "company": row[3]
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            findings["top_pain_points"] = {"error": str(e)}
        
        # Hair-on-fire problems
        try:
            cursor.execute("""
                SELECT description, intensity_score, frequency, company_name
                FROM pain_points
                WHERE hair_on_fire = 1
                ORDER BY intensity_score DESC
            """)
            
            findings["hair_on_fire_problems"] = [
                {
                    "description": row[0],
                    "intensity": row[1],
                    "frequency": row[2],
                    "company": row[3]
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            findings["hair_on_fire_problems"] = {"error": str(e)}
        
        # Quick win automation candidates
        try:
            cursor.execute("""
                SELECT name, priority_quadrant, effort_score, impact_score, company_name
                FROM automation_candidates
                WHERE priority_quadrant = 'Quick Win'
                ORDER BY impact_score DESC, effort_score ASC
                LIMIT 10
            """)
            
            findings["quick_wins"] = [
                {
                    "name": row[0],
                    "quadrant": row[1],
                    "effort": row[2],
                    "impact": row[3],
                    "company": row[4]
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            findings["quick_wins"] = {"error": str(e)}
        
        # Most mentioned systems
        try:
            cursor.execute("""
                SELECT name, COUNT(*) as mentions
                FROM systems
                GROUP BY name
                ORDER BY mentions DESC
                LIMIT 10
            """)
            
            findings["most_mentioned_systems"] = [
                {"system": row[0], "mentions": row[1]}
                for row in cursor.fetchall()
            ]
        except Exception as e:
            findings["most_mentioned_systems"] = {"error": str(e)}
        
        self.report["top_findings"] = findings
    
    def save_report(self, output_path: Path):
        """Save report to JSON file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Report saved to: {output_path}")
    
    def print_summary(self):
        """Print report summary to console"""
        print("\n" + "=" * 70)
        print("📊 EXTRACTION REPORT SUMMARY")
        print("=" * 70)
        
        # Extraction summary
        summary = self.report["extraction_summary"]
        print(f"\n📋 Interviews Processed: {summary['total_interviews']}")
        for company, count in summary.get("interviews_by_company", {}).items():
            print(f"  • {company}: {count}")
        
        # Entity statistics
        print(f"\n📈 Entities Extracted:")
        total_entities = 0
        for table, stats in self.report["entity_statistics"].items():
            if "error" not in stats:
                count = stats["total"]
                total_entities += count
                avg_conf = stats["avg_confidence_score"]
                needs_review = stats["needs_review"]
                print(f"  • {table:30s}: {count:4d} (avg conf: {avg_conf:.2f}, review: {needs_review})")
        
        print(f"\n  {'TOTAL':30s}: {total_entities:4d} entities")
        
        # Quality metrics
        quality = self.report["quality_metrics"]
        print(f"\n🔍 Quality Metrics:")
        for level, percentage in quality.get("confidence_percentages", {}).items():
            print(f"  • {level}: {percentage}%")
        
        # Top findings
        findings = self.report["top_findings"]
        
        if "hair_on_fire_problems" in findings and not isinstance(findings["hair_on_fire_problems"], dict):
            print(f"\n🔥 Hair-on-Fire Problems: {len(findings['hair_on_fire_problems'])}")
            for i, problem in enumerate(findings["hair_on_fire_problems"][:5], 1):
                print(f"  {i}. [{problem['company']}] {problem['description'][:60]}...")
        
        if "quick_wins" in findings and not isinstance(findings["quick_wins"], dict):
            print(f"\n⚡ Quick Win Opportunities: {len(findings['quick_wins'])}")
            for i, win in enumerate(findings["quick_wins"][:5], 1):
                print(f"  {i}. [{win['company']}] {win['name'][:60]}...")
        
        # CEO validation
        if "ceo_validation" in self.report and "error" not in self.report["ceo_validation"]:
            ceo = self.report["ceo_validation"]
            print(f"\n👔 CEO Validation:")
            print(f"  • Confirmed priorities: {ceo.get('confirmed_priorities', 0)}")
            print(f"  • Weak priorities: {ceo.get('weak_priorities', 0)}")
            print(f"  • Overlooked opportunities: {ceo.get('overlooked_opportunities', 0)}")
        
        # Cross-company insights
        if "cross_company_insights" in self.report and "error" not in self.report["cross_company_insights"]:
            cross = self.report["cross_company_insights"]
            print(f"\n🌐 Cross-Company Insights:")
            print(f"  • Common pain points: {cross.get('common_pain_points', 0)}")
            print(f"  • Standardization opportunities: {cross.get('standardization_opportunities', 0)}")


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate comprehensive extraction report')
    parser.add_argument('--db-path', type=Path, default=DB_PATH,
                       help=f'Database path (default: {DB_PATH})')
    parser.add_argument('--output', type=Path, 
                       default=REPORTS_DIR / "comprehensive_extraction_report.json",
                       help='Output report path')
    args = parser.parse_args()
    
    if not args.db_path.exists():
        print(f"❌ Database not found: {args.db_path}")
        print(f"   Run full_extraction_pipeline.py first")
        exit(1)
    
    print(f"📂 Database: {args.db_path}")
    print(f"📄 Output: {args.output}\n")
    
    # Generate report
    generator = ExtractionReportGenerator(args.db_path)
    report = generator.generate()
    
    # Save and print
    generator.save_report(args.output)
    generator.print_summary()
    
    print(f"\n✅ Comprehensive extraction report complete!")
    print(f"\nNext steps:")
    print(f"  1. Review report: {args.output}")
    print(f"  2. Check quality metrics and entities needing review")
    print(f"  3. Validate CEO assumptions and cross-company insights")


if __name__ == "__main__":
    main()
