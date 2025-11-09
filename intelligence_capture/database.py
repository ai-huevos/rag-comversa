"""
Database schema and operations for Intelligence Capture System
Based on PHASE1_ONTOLOGY_SCHEMA.json
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


def json_serialize(obj: Any) -> str:
    """
    Serialize object to JSON with proper UTF-8 handling for Spanish text
    
    Args:
        obj: Object to serialize (dict, list, etc.)
        
    Returns:
        JSON string with Spanish characters preserved
    """
    return json.dumps(obj, ensure_ascii=False)


class IntelligenceDB:
    """Manages SQLite database for captured intelligence"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to database with WAL mode for parallel processing"""
        self.conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,  # Wait up to 30s for locks
            check_same_thread=False  # Allow multi-threading
        )
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts
        # Ensure UTF-8 text handling (Python 3 default, but explicit is better)
        self.conn.text_factory = str
        
        # Enable WAL mode for concurrent access (parallel processing)
        self.conn.execute("PRAGMA journal_mode=WAL")
        
        # Set busy timeout (wait 5s if database is locked)
        self.conn.execute("PRAGMA busy_timeout=5000")
        
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys=ON")
        
        print("✓ Database connected with WAL mode (parallel-safe)")
        
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def init_schema(self):
        """Create all tables based on ontology schema"""
        cursor = self.conn.cursor()
        
        # Interviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                respondent TEXT NOT NULL,
                role TEXT NOT NULL,
                date TEXT NOT NULL,
                raw_data TEXT NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                extraction_status TEXT DEFAULT 'pending',
                extraction_attempts INTEGER DEFAULT 0,
                last_extraction_error TEXT,
                UNIQUE(respondent, company, date)
            )
        """)

        # Migrate existing interviews table if needed
        self._migrate_interviews_table(cursor)
        
        # Pain Points table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pain_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                company TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT NOT NULL,
                affected_roles TEXT,
                affected_processes TEXT,
                frequency TEXT,
                severity TEXT,
                impact_description TEXT,
                proposed_solutions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        
        # Processes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                company TEXT NOT NULL,
                name TEXT NOT NULL,
                owner TEXT NOT NULL,
                domain TEXT,
                description TEXT,
                inputs TEXT,
                outputs TEXT,
                systems TEXT,
                frequency TEXT,
                dependencies TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        
        # Systems table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                domain TEXT,
                vendor TEXT,
                type TEXT,
                companies_using TEXT,
                usage_count INTEGER DEFAULT 1,
                pain_points TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # KPIs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kpis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                company TEXT NOT NULL,
                name TEXT NOT NULL,
                domain TEXT,
                definition TEXT,
                formula TEXT,
                owner TEXT,
                data_source TEXT,
                baseline TEXT,
                target TEXT,
                cadence TEXT,
                related_processes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        
        # Automation Candidates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                company TEXT NOT NULL,
                name TEXT NOT NULL,
                process TEXT,
                trigger_event TEXT,
                action TEXT,
                output TEXT,
                owner TEXT,
                complexity TEXT,
                impact TEXT,
                effort_estimate TEXT,
                systems_involved TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        
        # Inefficiencies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inefficiencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                company TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT,
                frequency TEXT,
                time_wasted TEXT,
                related_process TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pain_points_company ON pain_points(company)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pain_points_severity ON pain_points(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processes_company ON processes(company)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kpis_company ON kpis(company)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_systems_name ON systems(name)")
        
        self.conn.commit()

    def _migrate_interviews_table(self, cursor):
        """Add progress tracking columns to existing interviews table"""
        try:
            # Check if columns already exist
            cursor.execute("PRAGMA table_info(interviews)")
            columns = [row[1] for row in cursor.fetchall()]

            # Add extraction_status if missing
            if "extraction_status" not in columns:
                cursor.execute("ALTER TABLE interviews ADD COLUMN extraction_status TEXT DEFAULT 'pending'")
                print("  ✓ Added extraction_status column")

            # Add extraction_attempts if missing
            if "extraction_attempts" not in columns:
                cursor.execute("ALTER TABLE interviews ADD COLUMN extraction_attempts INTEGER DEFAULT 0")
                print("  ✓ Added extraction_attempts column")

            # Add last_extraction_error if missing
            if "last_extraction_error" not in columns:
                cursor.execute("ALTER TABLE interviews ADD COLUMN last_extraction_error TEXT")
                print("  ✓ Added last_extraction_error column")

            self.conn.commit()

        except Exception as e:
            print(f"  ⚠️  Migration warning: {str(e)}")

    def update_extraction_status(self, interview_id: int, status: str, error: str = None):
        """
        Update extraction status for an interview

        Args:
            interview_id: ID of the interview
            status: 'pending', 'in_progress', 'complete', or 'failed'
            error: Error message if status is 'failed'
        """
        cursor = self.conn.cursor()

        if status == 'failed':
            cursor.execute("""
                UPDATE interviews
                SET extraction_status = ?,
                    extraction_attempts = extraction_attempts + 1,
                    last_extraction_error = ?
                WHERE id = ?
            """, (status, error, interview_id))
        else:
            cursor.execute("""
                UPDATE interviews
                SET extraction_status = ?,
                    extraction_attempts = extraction_attempts + 1
                WHERE id = ?
            """, (status, interview_id))

        self.conn.commit()

    def get_interviews_by_status(self, status: str = None) -> List[Dict]:
        """
        Get interviews filtered by extraction status

        Args:
            status: Filter by status ('pending', 'in_progress', 'complete', 'failed')
                   If None, returns all interviews

        Returns:
            List of interview dictionaries with metadata
        """
        cursor = self.conn.cursor()

        if status:
            cursor.execute("""
                SELECT id, company, respondent, role, date,
                       extraction_status, extraction_attempts, last_extraction_error
                FROM interviews
                WHERE extraction_status = ?
                ORDER BY id
            """, (status,))
        else:
            cursor.execute("""
                SELECT id, company, respondent, role, date,
                       extraction_status, extraction_attempts, last_extraction_error
                FROM interviews
                ORDER BY id
            """)

        rows = cursor.fetchall()
        interviews = []

        for row in rows:
            interviews.append({
                "id": row[0],
                "company": row[1],
                "respondent": row[2],
                "role": row[3],
                "date": row[4],
                "extraction_status": row[5] if len(row) > 5 else "pending",
                "extraction_attempts": row[6] if len(row) > 6 else 0,
                "last_extraction_error": row[7] if len(row) > 7 else None
            })

        return interviews

    def reset_extraction_status(self, status_filter: str = None):
        """
        Reset extraction status for interviews (useful for re-running extractions)

        Args:
            status_filter: Only reset interviews with this status (e.g., 'failed')
                          If None, resets all interviews
        """
        cursor = self.conn.cursor()

        if status_filter:
            cursor.execute("""
                UPDATE interviews
                SET extraction_status = 'pending',
                    last_extraction_error = NULL
                WHERE extraction_status = ?
            """, (status_filter,))
        else:
            cursor.execute("""
                UPDATE interviews
                SET extraction_status = 'pending',
                    extraction_attempts = 0,
                    last_extraction_error = NULL
            """)

        self.conn.commit()
        print(f"  ✓ Reset extraction status for {cursor.rowcount} interviews")

    def insert_interview(self, meta: Dict, qa_pairs: Dict) -> int:
        """Insert interview and return interview_id"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO interviews (company, respondent, role, date, raw_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            meta.get("company", "Unknown"),
            meta.get("respondent", "Unknown"),
            meta.get("role", "Unknown"),
            meta.get("date", "Unknown"),
            json_serialize({"meta": meta, "qa_pairs": qa_pairs})
        ))
        
        self.conn.commit()
        
        # Get the interview_id
        cursor.execute("""
            SELECT id FROM interviews 
            WHERE respondent = ? AND company = ? AND date = ?
        """, (meta.get("respondent"), meta.get("company", "Unknown"), meta.get("date")))
        
        result = cursor.fetchone()
        return result[0] if result else None
    
    def insert_pain_point(self, interview_id: int, company: str, pain_point: Dict):
        """Insert a pain point with optional review metrics"""
        cursor = self.conn.cursor()

        # Extract review metrics if available
        review_metrics = pain_point.get("_review_metrics", {})

        # Check if review fields exist in table
        cursor.execute("PRAGMA table_info(pain_points)")
        columns = [row[1] for row in cursor.fetchall()]
        has_review_fields = "review_quality_score" in columns

        if has_review_fields:
            cursor.execute("""
                INSERT INTO pain_points (
                    interview_id, company, type, description, affected_roles,
                    affected_processes, frequency, severity, impact_description,
                    proposed_solutions,
                    review_quality_score, review_accuracy_score, review_completeness_score,
                    review_relevance_score, review_consistency_score, review_hallucination_score,
                    review_consensus_level, review_needs_human, review_feedback,
                    review_model_agreement
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                interview_id,
                company,
                pain_point.get("type", "Unknown"),
                pain_point.get("description", ""),
                json_serialize(pain_point.get("affected_roles", [])),
                json_serialize(pain_point.get("affected_processes", [])),
                pain_point.get("frequency", "Unknown"),
                pain_point.get("severity", "Unknown"),
                pain_point.get("impact_description", ""),
                json_serialize(pain_point.get("proposed_solutions", [])),
                review_metrics.get("overall_quality", 0.0),
                review_metrics.get("accuracy_score", 0.0),
                review_metrics.get("completeness_score", 0.0),
                review_metrics.get("relevance_score", 0.0),
                review_metrics.get("consistency_score", 0.0),
                review_metrics.get("hallucination_score", 0.0),
                review_metrics.get("consensus_level", 0.0),
                1 if review_metrics.get("needs_human_review", False) else 0,
                review_metrics.get("review_feedback", ""),
                json_serialize(review_metrics.get("model_agreement", {}))
            ))
        else:
            # Fallback to original insert without review fields
            cursor.execute("""
                INSERT INTO pain_points (
                    interview_id, company, type, description, affected_roles,
                    affected_processes, frequency, severity, impact_description,
                    proposed_solutions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                interview_id,
                company,
                pain_point.get("type", "Unknown"),
                pain_point.get("description", ""),
                json_serialize(pain_point.get("affected_roles", [])),
                json_serialize(pain_point.get("affected_processes", [])),
                pain_point.get("frequency", "Unknown"),
                pain_point.get("severity", "Unknown"),
                pain_point.get("impact_description", ""),
                json_serialize(pain_point.get("proposed_solutions", []))
            ))

        self.conn.commit()
    
    def insert_process(self, interview_id: int, company: str, process: Dict):
        """Insert a process"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO processes (
                interview_id, company, name, owner, domain, description,
                inputs, outputs, systems, frequency, dependencies
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            process.get("name", ""),
            process.get("owner", ""),
            process.get("domain", ""),
            process.get("description", ""),
            json_serialize(process.get("inputs", [])),
            json_serialize(process.get("outputs", [])),
            json_serialize(process.get("systems", [])),
            process.get("frequency", ""),
            json_serialize(process.get("dependencies", []))
        ))
        
        self.conn.commit()
    
    def insert_or_update_system(self, system: Dict, company: str):
        """Insert or update a system"""
        cursor = self.conn.cursor()
        
        # Check if system exists
        cursor.execute("SELECT id, companies_using, usage_count FROM systems WHERE name = ?", 
                      (system.get("name"),))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing system
            system_id, companies_json, usage_count = existing
            companies = json.loads(companies_json) if companies_json else []
            if company not in companies:
                companies.append(company)
            
            cursor.execute("""
                UPDATE systems 
                SET companies_using = ?, usage_count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json_serialize(companies), usage_count + 1, system_id))
        else:
            # Insert new system
            cursor.execute("""
                INSERT INTO systems (name, domain, vendor, type, companies_using, pain_points)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                system.get("name", ""),
                system.get("domain", ""),
                system.get("vendor", ""),
                system.get("type", ""),
                json_serialize([company]),
                json_serialize(system.get("pain_points", []))
            ))
        
        self.conn.commit()
    
    def insert_kpi(self, interview_id: int, company: str, kpi: Dict):
        """Insert a KPI"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO kpis (
                interview_id, company, name, domain, definition, formula,
                owner, data_source, baseline, target, cadence, related_processes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            kpi.get("name", ""),
            kpi.get("domain", ""),
            kpi.get("definition", ""),
            kpi.get("formula", ""),
            kpi.get("owner", ""),
            kpi.get("data_source", ""),
            kpi.get("baseline", ""),
            kpi.get("target", ""),
            kpi.get("cadence", ""),
            json_serialize(kpi.get("related_processes", []))
        ))
        
        self.conn.commit()
    
    def insert_automation_candidate(self, interview_id: int, company: str, automation: Dict):
        """Insert an automation candidate"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO automation_candidates (
                interview_id, company, name, process, trigger_event, action,
                output, owner, complexity, impact, effort_estimate, systems_involved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            automation.get("name", ""),
            automation.get("process", ""),
            automation.get("trigger", ""),
            automation.get("action", ""),
            automation.get("output", ""),
            automation.get("owner", ""),
            automation.get("complexity", ""),
            automation.get("impact", ""),
            automation.get("effort_estimate", ""),
            json_serialize(automation.get("systems_involved", []))
        ))
        
        self.conn.commit()
    
    def insert_inefficiency(self, interview_id: int, company: str, inefficiency: Dict):
        """Insert an inefficiency"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO inefficiencies (
                interview_id, company, description, category, frequency,
                time_wasted, related_process
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            inefficiency.get("description", ""),
            inefficiency.get("category", ""),
            inefficiency.get("frequency", ""),
            inefficiency.get("time_wasted", ""),
            inefficiency.get("related_process", "")
        ))
        
        self.conn.commit()
    
    def insert_entities_batch(
        self,
        entity_type: str,
        entities: List[Dict],
        interview_id: int,
        company: str,
        business_unit: str = None
    ) -> Dict[str, Any]:
        """
        Batch insert multiple entities of the same type using transactions

        Args:
            entity_type: Type of entity (e.g., "pain_points", "processes")
            entities: List of entity dictionaries
            interview_id: Interview ID
            company: Company name
            business_unit: Business unit (for v2.0 entities)

        Returns:
            Dictionary with success status and error info
        """
        if not entities:
            return {"success": True, "inserted": 0, "errors": []}

        cursor = self.conn.cursor()
        inserted = 0
        errors = []

        try:
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")

            # Map entity type to insert method
            insert_methods = {
                "pain_points": self.insert_pain_point,
                "processes": self.insert_process,
                "systems": self.insert_or_update_system,
                "kpis": self.insert_kpi,
                "automation_candidates": self.insert_automation_candidate,
                "inefficiencies": self.insert_inefficiency,
                "communication_channels": self.insert_communication_channel,
                "decision_points": self.insert_decision_point,
                "data_flows": self.insert_data_flow,
                "temporal_patterns": self.insert_temporal_pattern,
                "failure_modes": self.insert_failure_mode,
                "team_structures": self.insert_team_structure,
                "knowledge_gaps": self.insert_knowledge_gap,
                "success_patterns": self.insert_success_pattern,
                "budget_constraints": self.insert_budget_constraint,
                "external_dependencies": self.insert_external_dependency,
                "pain_points_v2": self.insert_enhanced_pain_point,
                "systems_v2": self.insert_or_update_enhanced_system,
                "automation_candidates_v2": self.insert_enhanced_automation_candidate
            }

            insert_method = insert_methods.get(entity_type)
            if not insert_method:
                raise ValueError(f"Unknown entity type: {entity_type}")

            # Insert each entity
            for entity in entities:
                try:
                    # Call appropriate insert method based on entity type
                    if entity_type in ["systems", "systems_v2"]:
                        # Systems don't need interview_id
                        insert_method(entity, company)
                    elif entity_type in ["communication_channels", "decision_points", "data_flows",
                                       "temporal_patterns", "failure_modes", "team_structures",
                                       "knowledge_gaps", "success_patterns", "budget_constraints",
                                       "external_dependencies", "pain_points_v2", "automation_candidates_v2"]:
                        # v2.0 entities need business_unit
                        insert_method(interview_id, company, business_unit or "Unknown", entity)
                    else:
                        # v1.0 entities
                        insert_method(interview_id, company, entity)

                    inserted += 1

                except Exception as e:
                    errors.append(f"{entity.get('name', 'unknown')}: {str(e)[:100]}")

            # Commit transaction
            self.conn.commit()

            return {
                "success": len(errors) == 0,
                "inserted": inserted,
                "total": len(entities),
                "errors": errors
            }

        except Exception as e:
            # Rollback on error
            self.conn.rollback()
            return {
                "success": False,
                "inserted": 0,
                "total": len(entities),
                "errors": [f"Transaction failed: {str(e)}"]
            }

    def get_stats(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()

        stats = {}

        # Count by table
        for table in ["interviews", "pain_points", "processes", "systems", "kpis",
                     "automation_candidates", "inefficiencies"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]

        # Count by company
        cursor.execute("SELECT company, COUNT(*) FROM interviews GROUP BY company")
        stats["by_company"] = dict(cursor.fetchall())

        return stats



class EnhancedIntelligenceDB(IntelligenceDB):
    """
    Enhanced database with v2.0 schema supporting:
    - Multi-level organizational hierarchy
    - 10 new entity types
    - Enhanced v1.0 entities with additional fields
    - Confidence scoring and quality validation
    """
    
    def init_v2_schema(self):
        """
        Create v2.0 tables and enhance v1.0 tables
        Maintains backward compatibility - does not drop or modify existing data
        """
        cursor = self.conn.cursor()
        
        # First, ensure v1.0 schema exists
        self.init_schema()
        
        # Add v2.0 fields to existing interviews table
        self._add_column_if_not_exists('interviews', 'holding_name', 'TEXT DEFAULT "Comversa Group"')
        self._add_column_if_not_exists('interviews', 'business_unit', 'TEXT')
        self._add_column_if_not_exists('interviews', 'department', 'TEXT')
        self._add_column_if_not_exists('interviews', 'interview_method', 'TEXT DEFAULT "WhatsApp"')
        self._add_column_if_not_exists('interviews', 'interview_duration_minutes', 'INTEGER')
        self._add_column_if_not_exists('interviews', 'discovered_org_structure', 'TEXT')
        self._add_column_if_not_exists('interviews', 'org_structure_validated', 'INTEGER DEFAULT 0')
        self._add_column_if_not_exists('interviews', 'org_structure_confidence', 'REAL')
        self._add_column_if_not_exists('interviews', 'org_structure_deviations', 'TEXT')
        self._add_column_if_not_exists('interviews', 'suggested_follow_up_questions', 'TEXT')
        
        # Add v2.0 fields to pain_points table
        self._add_column_if_not_exists('pain_points', 'holding_name', 'TEXT DEFAULT "Comversa Group"')
        self._add_column_if_not_exists('pain_points', 'business_unit', 'TEXT')
        self._add_column_if_not_exists('pain_points', 'department', 'TEXT')
        self._add_column_if_not_exists('pain_points', 'intensity_score', 'INTEGER')
        self._add_column_if_not_exists('pain_points', 'hair_on_fire', 'INTEGER DEFAULT 0')
        self._add_column_if_not_exists('pain_points', 'time_wasted_per_occurrence_minutes', 'INTEGER')
        self._add_column_if_not_exists('pain_points', 'cost_impact_monthly_usd', 'REAL')
        self._add_column_if_not_exists('pain_points', 'estimated_annual_cost_usd', 'REAL')
        self._add_column_if_not_exists('pain_points', 'jtbd_who', 'TEXT')
        self._add_column_if_not_exists('pain_points', 'jtbd_what', 'TEXT')
        self._add_column_if_not_exists('pain_points', 'jtbd_where', 'TEXT')
        self._add_column_if_not_exists('pain_points', 'jtbd_formatted', 'TEXT')
        self._add_column_if_not_exists('pain_points', 'root_cause', 'TEXT')
        self._add_column_if_not_exists('pain_points', 'current_workaround', 'TEXT')
        self._add_column_if_not_exists('pain_points', 'confidence_score', 'REAL')
        self._add_column_if_not_exists('pain_points', 'needs_review', 'INTEGER DEFAULT 0')
        self._add_column_if_not_exists('pain_points', 'extraction_source', 'TEXT')
        self._add_column_if_not_exists('pain_points', 'extraction_reasoning', 'TEXT')
        
        # Add v2.0 fields to processes table
        self._add_column_if_not_exists('processes', 'holding_name', 'TEXT DEFAULT "Comversa Group"')
        self._add_column_if_not_exists('processes', 'business_unit', 'TEXT')
        self._add_column_if_not_exists('processes', 'department', 'TEXT')
        self._add_column_if_not_exists('processes', 'industry_context', 'TEXT')
        self._add_column_if_not_exists('processes', 'communication_methods', 'TEXT')
        self._add_column_if_not_exists('processes', 'decision_points', 'TEXT')
        self._add_column_if_not_exists('processes', 'failure_modes', 'TEXT')
        self._add_column_if_not_exists('processes', 'temporal_patterns', 'TEXT')
        self._add_column_if_not_exists('processes', 'confidence_score', 'REAL')
        self._add_column_if_not_exists('processes', 'needs_review', 'INTEGER DEFAULT 0')
        self._add_column_if_not_exists('processes', 'extraction_source', 'TEXT')
        
        # Add v2.0 fields to systems table
        self._add_column_if_not_exists('systems', 'integration_pain_points', 'TEXT')
        self._add_column_if_not_exists('systems', 'data_quality_issues', 'TEXT')
        self._add_column_if_not_exists('systems', 'user_satisfaction_score', 'REAL')
        self._add_column_if_not_exists('systems', 'replacement_candidate', 'INTEGER DEFAULT 0')
        self._add_column_if_not_exists('systems', 'adoption_rate', 'REAL')
        
        # Add v2.0 fields to automation_candidates table
        self._add_column_if_not_exists('automation_candidates', 'holding_name', 'TEXT DEFAULT "Comversa Group"')
        self._add_column_if_not_exists('automation_candidates', 'business_unit', 'TEXT')
        self._add_column_if_not_exists('automation_candidates', 'department', 'TEXT')
        self._add_column_if_not_exists('automation_candidates', 'current_manual_process_description', 'TEXT')
        self._add_column_if_not_exists('automation_candidates', 'data_sources_needed', 'TEXT')
        self._add_column_if_not_exists('automation_candidates', 'approval_required', 'INTEGER DEFAULT 0')
        self._add_column_if_not_exists('automation_candidates', 'approval_threshold_usd', 'REAL')
        self._add_column_if_not_exists('automation_candidates', 'monitoring_metrics', 'TEXT')
        self._add_column_if_not_exists('automation_candidates', 'effort_score', 'INTEGER')
        self._add_column_if_not_exists('automation_candidates', 'impact_score', 'INTEGER')
        self._add_column_if_not_exists('automation_candidates', 'priority_quadrant', 'TEXT')
        self._add_column_if_not_exists('automation_candidates', 'estimated_roi_months', 'REAL')
        self._add_column_if_not_exists('automation_candidates', 'estimated_annual_savings_usd', 'REAL')
        self._add_column_if_not_exists('automation_candidates', 'ceo_priority', 'INTEGER DEFAULT 0')
        self._add_column_if_not_exists('automation_candidates', 'overlooked_opportunity', 'INTEGER DEFAULT 0')
        self._add_column_if_not_exists('automation_candidates', 'data_support_score', 'REAL')
        self._add_column_if_not_exists('automation_candidates', 'confidence_score', 'REAL')
        self._add_column_if_not_exists('automation_candidates', 'needs_review', 'INTEGER DEFAULT 0')
        self._add_column_if_not_exists('automation_candidates', 'extraction_source', 'TEXT')
        
        # Create new v2.0 entity tables
        self._create_communication_channels_table()
        self._create_decision_points_table()
        self._create_data_flows_table()
        self._create_temporal_patterns_table()
        self._create_failure_modes_table()
        self._create_team_structures_table()
        self._create_knowledge_gaps_table()
        self._create_success_patterns_table()
        self._create_budget_constraints_table()
        self._create_external_dependencies_table()
        
        # Create indexes for v2.0 queries
        self._create_v2_indexes()
        
        self.conn.commit()
        print("✅ v2.0 schema initialized successfully")
    
    def _add_column_if_not_exists(self, table: str, column: str, column_type: str):
        """Add column to table if it doesn't already exist"""
        cursor = self.conn.cursor()

        # Check if column exists
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]

        if column not in columns:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                print(f"  Added column {table}.{column}")
            except sqlite3.OperationalError as e:
                print(f"  Warning: Could not add {table}.{column}: {e}")

    def add_ensemble_review_fields(self):
        """
        Add ensemble validation tracking fields to all entity tables
        For forensic-grade quality review system
        """
        print("\n🔬 Adding ensemble review tracking fields...")

        # Tables to enhance with review fields
        entity_tables = [
            "pain_points",
            "processes",
            "systems",
            "kpis",
            "automation_candidates",
            "inefficiencies",
            "communication_channels",
            "decision_points",
            "data_flows",
            "temporal_patterns",
            "failure_modes",
            "team_structures",
            "knowledge_gaps",
            "success_patterns",
            "budget_constraints",
            "external_dependencies"
        ]

        # Ensemble review fields
        review_fields = [
            ("review_quality_score", "REAL DEFAULT 0.0"),           # Overall quality 0.0-1.0
            ("review_accuracy_score", "REAL DEFAULT 0.0"),          # Accuracy vs source
            ("review_completeness_score", "REAL DEFAULT 0.0"),      # Completeness
            ("review_relevance_score", "REAL DEFAULT 0.0"),         # Relevance
            ("review_consistency_score", "REAL DEFAULT 0.0"),       # Internal consistency
            ("review_hallucination_score", "REAL DEFAULT 0.0"),     # 1.0=no hallucination, 0.0=high
            ("review_consensus_level", "REAL DEFAULT 0.0"),         # Agreement across models
            ("review_needs_human", "INTEGER DEFAULT 0"),            # Flag for human review
            ("review_feedback", "TEXT"),                            # Structured feedback
            ("review_model_agreement", "TEXT"),                     # JSON: model agreement data
            ("review_iteration_count", "INTEGER DEFAULT 0"),        # Refinement iterations
            ("review_ensemble_models", "TEXT"),                     # JSON: models used
            ("review_cost_usd", "REAL DEFAULT 0.0"),               # Estimated API cost
            ("final_approved", "INTEGER DEFAULT 0"),                # Human approval flag
        ]

        # Add fields to each table
        for table in entity_tables:
            # Check if table exists
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            if not cursor.fetchone():
                print(f"  ⊘ Table {table} doesn't exist, skipping")
                continue

            print(f"  Enhancing {table}...")
            for field_name, field_type in review_fields:
                self._add_column_if_not_exists(table, field_name, field_type)

        self.conn.commit()
        print("✅ Ensemble review fields added successfully")
    
    def add_consolidation_schema(self):
        """
        Add Knowledge Graph consolidation tracking fields to all entity tables
        and create new tables for relationships, audit trail, and patterns.
        
        This enables:
        - Duplicate entity detection and merging
        - Source tracking across interviews
        - Consensus confidence scoring
        - Relationship discovery between entities
        - Pattern recognition across interviews
        """
        print("\n🔗 Adding Knowledge Graph consolidation schema...")
        
        # All entity tables that need consolidation tracking
        entity_tables = [
            "pain_points",
            "processes",
            "systems",
            "kpis",
            "automation_candidates",
            "inefficiencies",
            "communication_channels",
            "decision_points",
            "data_flows",
            "temporal_patterns",
            "failure_modes",
            "team_structures",
            "knowledge_gaps",
            "success_patterns",
            "budget_constraints",
            "external_dependencies",
            "interviews"  # Also track consolidation for interviews
        ]
        
        # Consolidation tracking fields
        consolidation_fields = [
            ("mentioned_in_interviews", "TEXT"),                    # JSON array of interview IDs
            ("source_count", "INTEGER DEFAULT 1"),                  # Number of interviews mentioning this
            ("consensus_confidence", "REAL DEFAULT 1.0"),           # Confidence score 0.0-1.0
            ("is_consolidated", "INTEGER DEFAULT 0"),               # Boolean: has been merged
            ("has_contradictions", "INTEGER DEFAULT 0"),            # Boolean: conflicting data found
            ("contradiction_details", "TEXT"),                      # JSON: details of contradictions
            ("merged_entity_ids", "TEXT"),                          # JSON: IDs of entities merged into this
            ("first_mentioned_date", "TEXT"),                       # First interview date
            ("last_mentioned_date", "TEXT"),                        # Most recent interview date
            ("consolidated_at", "TIMESTAMP"),                       # When consolidation happened
        ]
        
        # Add consolidation fields to all entity tables
        for table in entity_tables:
            # Check if table exists
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            if not cursor.fetchone():
                print(f"  ⊘ Table {table} doesn't exist, skipping")
                continue
            
            print(f"  Adding consolidation fields to {table}...")
            for field_name, field_type in consolidation_fields:
                self._add_column_if_not_exists(table, field_name, field_type)
        
        # Create relationships table
        print("\n  Creating relationships table...")
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entity_id INTEGER NOT NULL,
                source_entity_type TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                target_entity_id INTEGER NOT NULL,
                target_entity_type TEXT NOT NULL,
                strength REAL DEFAULT 0.8,
                mentioned_in_interviews TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created relationships table")
        
        # Create consolidation_audit table
        print("  Creating consolidation_audit table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consolidation_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                merged_entity_ids TEXT NOT NULL,
                resulting_entity_id INTEGER NOT NULL,
                similarity_score REAL NOT NULL,
                consolidation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rollback_timestamp TIMESTAMP,
                rollback_reason TEXT
            )
        """)
        print("  ✓ Created consolidation_audit table")
        
        # Create patterns table
        print("  Creating patterns table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                pattern_frequency REAL NOT NULL,
                source_count INTEGER NOT NULL,
                high_priority INTEGER DEFAULT 0,
                description TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created patterns table")
        
        # Create indexes for performance
        print("\n  Creating indexes for consolidation queries...")
        
        # Relationship indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_source 
            ON relationships(source_entity_id, source_entity_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_target 
            ON relationships(target_entity_id, target_entity_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_type 
            ON relationships(relationship_type)
        """)
        
        # Audit indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_entity_type 
            ON consolidation_audit(entity_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
            ON consolidation_audit(consolidation_timestamp)
        """)
        
        # Pattern indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_type 
            ON patterns(pattern_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_priority 
            ON patterns(high_priority)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_entity 
            ON patterns(entity_type, entity_id)
        """)
        
        # Entity name indexes for duplicate detection (if not already exist)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pain_points_description 
            ON pain_points(description)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_processes_name 
            ON processes(name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_systems_name_consolidated 
            ON systems(name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_kpis_name 
            ON kpis(name)
        """)
        
        print("  ✓ Created all indexes")
        
        self.conn.commit()
        print("\n✅ Knowledge Graph consolidation schema added successfully")
    
    def _create_communication_channels_table(self):
        """Create communication_channels table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS communication_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                holding_name TEXT DEFAULT 'Comversa Group',
                company_name TEXT NOT NULL,
                business_unit TEXT,
                department TEXT,
                channel_name TEXT NOT NULL,
                purpose TEXT,
                frequency TEXT,
                participants TEXT,
                response_sla_minutes INTEGER,
                pain_points TEXT,
                related_processes TEXT,
                confidence_score REAL,
                needs_review INTEGER DEFAULT 0,
                extraction_source TEXT,
                extraction_reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        print("  Created communication_channels table")
    
    def _create_decision_points_table(self):
        """Create decision_points table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                holding_name TEXT DEFAULT 'Comversa Group',
                company_name TEXT NOT NULL,
                business_unit TEXT,
                department TEXT,
                decision_type TEXT NOT NULL,
                decision_maker_role TEXT NOT NULL,
                decision_criteria TEXT,
                approval_required INTEGER DEFAULT 0,
                approval_threshold TEXT,
                authority_limit_usd REAL,
                escalation_trigger TEXT,
                escalation_to_role TEXT,
                related_process TEXT,
                confidence_score REAL,
                needs_review INTEGER DEFAULT 0,
                extraction_source TEXT,
                extraction_reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        print("  Created decision_points table")
    
    def _create_data_flows_table(self):
        """Create data_flows table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_flows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                holding_name TEXT DEFAULT 'Comversa Group',
                company_name TEXT NOT NULL,
                business_unit TEXT,
                department TEXT,
                source_system TEXT NOT NULL,
                target_system TEXT NOT NULL,
                data_type TEXT,
                transfer_method TEXT,
                transfer_frequency TEXT,
                data_quality_issues TEXT,
                pain_points TEXT,
                related_process TEXT,
                confidence_score REAL,
                needs_review INTEGER DEFAULT 0,
                extraction_source TEXT,
                extraction_reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        print("  Created data_flows table")
    
    def _create_temporal_patterns_table(self):
        """Create temporal_patterns table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temporal_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                holding_name TEXT DEFAULT 'Comversa Group',
                company_name TEXT NOT NULL,
                business_unit TEXT,
                department TEXT,
                activity_name TEXT NOT NULL,
                frequency TEXT,
                time_of_day TEXT,
                duration_minutes INTEGER,
                participants TEXT,
                triggers_actions TEXT,
                related_process TEXT,
                confidence_score REAL,
                needs_review INTEGER DEFAULT 0,
                extraction_source TEXT,
                extraction_reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        print("  Created temporal_patterns table")
    
    def _create_failure_modes_table(self):
        """Create failure_modes table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failure_modes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                holding_name TEXT DEFAULT 'Comversa Group',
                company_name TEXT NOT NULL,
                business_unit TEXT,
                department TEXT,
                failure_description TEXT NOT NULL,
                frequency TEXT,
                impact_description TEXT,
                root_cause TEXT,
                current_workaround TEXT,
                recovery_time_minutes INTEGER,
                proposed_prevention TEXT,
                related_process TEXT,
                related_automation_candidate_id INTEGER,
                confidence_score REAL,
                needs_review INTEGER DEFAULT 0,
                extraction_source TEXT,
                extraction_reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        print("  Created failure_modes table")
    
    def _create_team_structures_table(self):
        """Create team_structures table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_structures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                holding_name TEXT DEFAULT 'Comversa Group',
                company_name TEXT NOT NULL,
                business_unit TEXT,
                department TEXT,
                role TEXT NOT NULL,
                team_size INTEGER,
                reports_to TEXT,
                coordinates_with TEXT,
                external_dependencies TEXT,
                confidence_score REAL,
                needs_review INTEGER DEFAULT 0,
                extraction_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        print("  Created team_structures table")
    
    def _create_knowledge_gaps_table(self):
        """Create knowledge_gaps table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                holding_name TEXT DEFAULT 'Comversa Group',
                company_name TEXT NOT NULL,
                business_unit TEXT,
                department TEXT,
                area TEXT NOT NULL,
                affected_roles TEXT,
                impact TEXT,
                training_needed TEXT,
                confidence_score REAL,
                needs_review INTEGER DEFAULT 0,
                extraction_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        print("  Created knowledge_gaps table")
    
    def _create_success_patterns_table(self):
        """Create success_patterns table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS success_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                holding_name TEXT DEFAULT 'Comversa Group',
                company_name TEXT NOT NULL,
                business_unit TEXT,
                department TEXT,
                pattern TEXT NOT NULL,
                role TEXT,
                benefit TEXT,
                replicable_to TEXT,
                confidence_score REAL,
                needs_review INTEGER DEFAULT 0,
                extraction_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        print("  Created success_patterns table")
    
    def _create_budget_constraints_table(self):
        """Create budget_constraints table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budget_constraints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                holding_name TEXT DEFAULT 'Comversa Group',
                company_name TEXT NOT NULL,
                business_unit TEXT,
                department TEXT,
                area TEXT NOT NULL,
                budget_type TEXT,
                approval_required_above REAL,
                approver TEXT,
                pain_point TEXT,
                confidence_score REAL,
                needs_review INTEGER DEFAULT 0,
                extraction_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        print("  Created budget_constraints table")
    
    def _create_external_dependencies_table(self):
        """Create external_dependencies table"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS external_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                holding_name TEXT DEFAULT 'Comversa Group',
                company_name TEXT NOT NULL,
                business_unit TEXT,
                department TEXT,
                vendor TEXT NOT NULL,
                service TEXT NOT NULL,
                frequency TEXT,
                coordinator TEXT,
                sla TEXT,
                payment_process TEXT,
                confidence_score REAL,
                needs_review INTEGER DEFAULT 0,
                extraction_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews(id)
            )
        """)
        print("  Created external_dependencies table")
    
    def _create_v2_indexes(self):
        """Create indexes for v2.0 queries"""
        cursor = self.conn.cursor()
        
        # Organizational hierarchy indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interviews_company_bu ON interviews(company, business_unit)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pain_points_company_bu ON pain_points(company, business_unit)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processes_company_bu ON processes(company, business_unit)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_automation_candidates_company_bu ON automation_candidates(company, business_unit)")
        
        # Quality and validation indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pain_points_needs_review ON pain_points(needs_review)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pain_points_hair_on_fire ON pain_points(hair_on_fire)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_automation_candidates_priority ON automation_candidates(priority_quadrant)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_automation_candidates_ceo_priority ON automation_candidates(ceo_priority)")
        
        # New entity indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_communication_channels_company ON communication_channels(company_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision_points_company ON decision_points(company_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_flows_company ON data_flows(company_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_temporal_patterns_company ON temporal_patterns(company_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_failure_modes_company ON failure_modes(company_name)")
        
        print("  Created v2.0 indexes")
    
    def query_by_company(self, company_name: str, entity_type: str, filters: Dict = None) -> List[Dict]:
        """
        Query entities for a specific company
        
        Args:
            company_name: Name of company to query
            entity_type: Type of entity (e.g., 'pain_point', 'process', 'communication_channel')
            filters: Optional additional filters
            
        Returns:
            List of entities matching criteria
        """
        cursor = self.conn.cursor()
        
        # Map entity type to table name
        table_map = {
            'pain_point': 'pain_points',
            'process': 'processes',
            'system': 'systems',
            'kpi': 'kpis',
            'automation_candidate': 'automation_candidates',
            'inefficiency': 'inefficiencies',
            'communication_channel': 'communication_channels',
            'decision_point': 'decision_points',
            'data_flow': 'data_flows',
            'temporal_pattern': 'temporal_patterns',
            'failure_mode': 'failure_modes',
            'team_structure': 'team_structures',
            'knowledge_gap': 'knowledge_gaps',
            'success_pattern': 'success_patterns',
            'budget_constraint': 'budget_constraints',
            'external_dependency': 'external_dependencies'
        }
        
        table = table_map.get(entity_type)
        if not table:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        # Build query - handle both company and company_name columns
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'company_name' in columns:
            query = f"SELECT * FROM {table} WHERE company_name = ?"
            params = [company_name]
        elif 'company' in columns:
            query = f"SELECT * FROM {table} WHERE company = ?"
            params = [company_name]
        else:
            raise ValueError(f"Table {table} has no company or company_name column")
        
        # Add additional filters
        if filters:
            for key, value in filters.items():
                query += f" AND {key} = ?"
                params.append(value)
        
        cursor.execute(query, params)
        
        # Convert rows to dicts
        columns = [description[0] for description in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def query_cross_company(self, entity_type: str, aggregation: str = "count") -> Dict:
        """
        Aggregate entities across all companies
        
        Args:
            entity_type: Type of entity to aggregate
            aggregation: Type of aggregation ('count', 'list')
            
        Returns:
            Dictionary with company names as keys
        """
        cursor = self.conn.cursor()
        
        table_map = {
            'pain_point': 'pain_points',
            'process': 'processes',
            'automation_candidate': 'automation_candidates',
            'communication_channel': 'communication_channels',
            'decision_point': 'decision_points',
            'data_flow': 'data_flows',
            'temporal_pattern': 'temporal_patterns',
            'failure_mode': 'failure_modes'
        }
        
        table = table_map.get(entity_type)
        if not table:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        # Check which column exists
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        company_col = 'company_name' if 'company_name' in columns else 'company'
        
        if aggregation == "count":
            # Count by company
            query = f"""
                SELECT {company_col} as company, COUNT(*) as count 
                FROM {table} 
                GROUP BY {company_col}
            """
            cursor.execute(query)
            return dict(cursor.fetchall())
        
        elif aggregation == "list":
            # List all entities by company
            query = f"SELECT * FROM {table}"
            cursor.execute(query)
            
            results = {}
            col_names = [description[0] for description in cursor.description]
            for row in cursor.fetchall():
                row_dict = dict(zip(col_names, row))
                company = row_dict.get('company_name') or row_dict.get('company')
                if company not in results:
                    results[company] = []
                results[company].append(row_dict)
            
            return results
        
        else:
            raise ValueError(f"Unknown aggregation type: {aggregation}")
    
    def get_v2_stats(self) -> Dict:
        """Get comprehensive v2.0 database statistics"""
        cursor = self.conn.cursor()
        
        stats = self.get_stats()  # Get v1.0 stats first
        
        # Add v2.0 entity counts
        v2_tables = [
            'communication_channels', 'decision_points', 'data_flows',
            'temporal_patterns', 'failure_modes', 'team_structures',
            'knowledge_gaps', 'success_patterns', 'budget_constraints',
            'external_dependencies'
        ]
        
        for table in v2_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        # Count entities needing review
        cursor.execute("SELECT COUNT(*) FROM pain_points WHERE needs_review = 1")
        stats['pain_points_needing_review'] = cursor.fetchone()[0]
        
        # Count hair-on-fire problems
        cursor.execute("SELECT COUNT(*) FROM pain_points WHERE hair_on_fire = 1")
        stats['hair_on_fire_problems'] = cursor.fetchone()[0]
        
        # Count by priority quadrant
        cursor.execute("""
            SELECT priority_quadrant, COUNT(*) 
            FROM automation_candidates 
            WHERE priority_quadrant IS NOT NULL
            GROUP BY priority_quadrant
        """)
        stats['by_priority_quadrant'] = dict(cursor.fetchall())
        
        # Count CEO priorities
        cursor.execute("SELECT COUNT(*) FROM automation_candidates WHERE ceo_priority = 1")
        stats['ceo_priorities'] = cursor.fetchone()[0]
        
        # Count overlooked opportunities
        cursor.execute("SELECT COUNT(*) FROM automation_candidates WHERE overlooked_opportunity = 1")
        stats['overlooked_opportunities'] = cursor.fetchone()[0]
        
        return stats

    
    def insert_communication_channel(self, interview_id: int, company: str, business_unit: str, channel: Dict):
        """Insert a communication channel entity"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO communication_channels (
                interview_id, company_name, business_unit, department,
                channel_name, purpose, frequency, participants,
                response_sla_minutes, pain_points, related_processes,
                confidence_score, needs_review, extraction_source, extraction_reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            business_unit,
            channel.get("department"),
            channel.get("channel_name", ""),
            channel.get("purpose", ""),
            channel.get("frequency", ""),
            json_serialize(channel.get("participants", [])),
            channel.get("response_sla_minutes"),
            json_serialize(channel.get("pain_points", [])),
            json_serialize(channel.get("related_processes", [])),
            channel.get("confidence_score", 0.0),
            1 if channel.get("confidence_score", 1.0) < 0.7 else 0,
            channel.get("extraction_source", ""),
            channel.get("extraction_reasoning", "")
        ))
        
        self.conn.commit()

    
    def insert_decision_point(self, interview_id: int, company: str, business_unit: str, decision: Dict):
        """Insert a decision point entity"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO decision_points (
                interview_id, company_name, business_unit, department,
                decision_type, decision_maker_role, decision_criteria,
                approval_required, approval_threshold, authority_limit_usd,
                escalation_trigger, escalation_to_role, related_process,
                confidence_score, needs_review, extraction_source, extraction_reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            business_unit,
            decision.get("department"),
            decision.get("decision_type", ""),
            decision.get("decision_maker_role", ""),
            json_serialize(decision.get("decision_criteria", [])),
            1 if decision.get("approval_required") else 0,
            decision.get("approval_threshold"),
            decision.get("authority_limit_usd"),
            decision.get("escalation_trigger"),
            decision.get("escalation_to_role"),
            decision.get("related_process"),
            decision.get("confidence_score", 0.0),
            1 if decision.get("confidence_score", 1.0) < 0.7 else 0,
            decision.get("extraction_source", ""),
            decision.get("extraction_reasoning", "")
        ))
        
        self.conn.commit()


    
    def insert_data_flow(self, interview_id: int, company: str, business_unit: str, flow: Dict):
        """Insert a data flow entity"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO data_flows (
                interview_id, company_name, business_unit, department,
                source_system, target_system, data_type, transfer_method,
                transfer_frequency, data_quality_issues, pain_points,
                related_process, confidence_score, needs_review,
                extraction_source, extraction_reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            business_unit,
            flow.get("department"),
            flow.get("source_system", ""),
            flow.get("target_system", ""),
            flow.get("data_type", ""),
            flow.get("transfer_method", ""),
            flow.get("transfer_frequency", ""),
            json_serialize(flow.get("data_quality_issues", [])),
            json_serialize(flow.get("pain_points", [])),
            flow.get("related_process"),
            flow.get("confidence_score", 0.0),
            1 if flow.get("confidence_score", 1.0) < 0.7 else 0,
            flow.get("extraction_source", ""),
            flow.get("extraction_reasoning", "")
        ))
        
        self.conn.commit()


    
    def insert_temporal_pattern(self, interview_id: int, company: str, business_unit: str, pattern: Dict):
        """Insert a temporal pattern entity"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO temporal_patterns (
                interview_id, company_name, business_unit, department,
                activity_name, frequency, time_of_day, duration_minutes,
                participants, triggers_actions, related_process,
                confidence_score, needs_review, extraction_source, extraction_reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            business_unit,
            pattern.get("department"),
            pattern.get("activity_name", ""),
            pattern.get("frequency", ""),
            pattern.get("time_of_day"),
            pattern.get("duration_minutes"),
            json_serialize(pattern.get("participants", [])),
            json_serialize(pattern.get("triggers_actions", [])),
            pattern.get("related_process"),
            pattern.get("confidence_score", 0.0),
            1 if pattern.get("confidence_score", 1.0) < 0.7 else 0,
            pattern.get("extraction_source", ""),
            pattern.get("extraction_reasoning", "")
        ))
        
        self.conn.commit()


    
    def insert_failure_mode(self, interview_id: int, company: str, business_unit: str, failure: Dict):
        """Insert a failure mode entity"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO failure_modes (
                interview_id, company_name, business_unit, department,
                failure_description, frequency, impact_description,
                root_cause, current_workaround, recovery_time_minutes,
                proposed_prevention, related_process, related_automation_candidate_id,
                confidence_score, needs_review, extraction_source, extraction_reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            business_unit,
            failure.get("department"),
            failure.get("failure_description", ""),
            failure.get("frequency", ""),
            failure.get("impact_description", ""),
            failure.get("root_cause"),
            failure.get("current_workaround"),
            failure.get("recovery_time_minutes"),
            failure.get("proposed_prevention"),
            failure.get("related_process"),
            failure.get("related_automation_candidate_id"),
            failure.get("confidence_score", 0.0),
            1 if failure.get("confidence_score", 1.0) < 0.7 else 0,
            failure.get("extraction_source", ""),
            failure.get("extraction_reasoning", "")
        ))
        
        self.conn.commit()


    
    def insert_enhanced_pain_point(self, interview_id: int, company: str, business_unit: str, pain_point: Dict):
        """Insert an enhanced pain point entity with v2.0 fields"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO pain_points (
                interview_id, company, business_unit, department,
                type, description, affected_roles, affected_processes,
                frequency, severity, impact_description, proposed_solutions,
                intensity_score, hair_on_fire, time_wasted_per_occurrence_minutes,
                cost_impact_monthly_usd, estimated_annual_cost_usd,
                jtbd_who, jtbd_what, jtbd_where, jtbd_formatted,
                root_cause, current_workaround,
                confidence_score, needs_review, extraction_source, extraction_reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            business_unit,
            pain_point.get("department"),
            pain_point.get("type", "Process Inefficiency"),
            pain_point.get("description", ""),
            json_serialize(pain_point.get("affected_roles", [])),
            json_serialize(pain_point.get("affected_processes", [])),
            pain_point.get("frequency", "Ad-hoc"),
            pain_point.get("severity", "Medium"),
            pain_point.get("impact_description", ""),
            json_serialize(pain_point.get("proposed_solutions", [])),
            pain_point.get("intensity_score", 5),
            1 if pain_point.get("hair_on_fire") else 0,
            pain_point.get("time_wasted_per_occurrence_minutes"),
            pain_point.get("cost_impact_monthly_usd"),
            pain_point.get("estimated_annual_cost_usd"),
            pain_point.get("jtbd_who"),
            pain_point.get("jtbd_what"),
            pain_point.get("jtbd_where"),
            pain_point.get("jtbd_formatted"),
            pain_point.get("root_cause"),
            pain_point.get("current_workaround"),
            pain_point.get("confidence_score", 0.0),
            1 if pain_point.get("confidence_score", 1.0) < 0.7 else 0,
            pain_point.get("extraction_source", ""),
            pain_point.get("extraction_reasoning", "")
        ))
        
        self.conn.commit()
    
    def insert_or_update_enhanced_system(self, system: Dict, company: str):
        """Insert or update an enhanced system with v2.0 fields"""
        cursor = self.conn.cursor()
        
        # Check if system exists
        cursor.execute("SELECT id, companies_using, usage_count FROM systems WHERE name = ?", 
                      (system.get("name"),))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing system
            system_id, companies_json, usage_count = existing
            companies = json.loads(companies_json) if companies_json else []
            if company not in companies:
                companies.append(company)
            
            # Merge pain points and integration issues
            cursor.execute("SELECT pain_points, integration_pain_points, data_quality_issues FROM systems WHERE id = ?", (system_id,))
            row = cursor.fetchone()
            existing_pain_points = json.loads(row[0]) if row[0] else []
            existing_integration_pain_points = json.loads(row[1]) if row[1] else []
            existing_data_quality_issues = json.loads(row[2]) if row[2] else []
            
            # Merge new pain points
            new_pain_points = system.get("pain_points", [])
            new_integration_pain_points = system.get("integration_pain_points", [])
            new_data_quality_issues = system.get("data_quality_issues", [])
            
            merged_pain_points = list(set(existing_pain_points + new_pain_points))
            merged_integration_pain_points = list(set(existing_integration_pain_points + new_integration_pain_points))
            merged_data_quality_issues = list(set(existing_data_quality_issues + new_data_quality_issues))
            
            # Update with merged data
            cursor.execute("""
                UPDATE systems 
                SET companies_using = ?, 
                    usage_count = ?,
                    pain_points = ?,
                    integration_pain_points = ?,
                    data_quality_issues = ?,
                    user_satisfaction_score = ?,
                    replacement_candidate = ?,
                    adoption_rate = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                json_serialize(companies), 
                usage_count + 1,
                json_serialize(merged_pain_points),
                json_serialize(merged_integration_pain_points),
                json_serialize(merged_data_quality_issues),
                system.get("user_satisfaction_score"),
                1 if system.get("replacement_candidate") else 0,
                system.get("adoption_rate"),
                system_id
            ))
        else:
            # Insert new system
            cursor.execute("""
                INSERT INTO systems (
                    name, domain, vendor, type, companies_using, pain_points,
                    integration_pain_points, data_quality_issues,
                    user_satisfaction_score, replacement_candidate, adoption_rate
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                system.get("name", ""),
                system.get("domain", ""),
                system.get("vendor", ""),
                system.get("type", ""),
                json_serialize([company]),
                json_serialize(system.get("pain_points", [])),
                json_serialize(system.get("integration_pain_points", [])),
                json_serialize(system.get("data_quality_issues", [])),
                system.get("user_satisfaction_score"),
                1 if system.get("replacement_candidate") else 0,
                system.get("adoption_rate")
            ))
        
        self.conn.commit()

    
    def insert_enhanced_automation_candidate(self, interview_id: int, company: str, business_unit: str, candidate: Dict):
        """Insert an enhanced automation candidate entity with v2.0 fields"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO automation_candidates (
                interview_id, company, business_unit, department,
                name, process, trigger_event, action, output, owner,
                complexity, impact, effort_estimate, systems_involved,
                current_manual_process_description, data_sources_needed,
                approval_required, approval_threshold_usd, monitoring_metrics,
                effort_score, impact_score, priority_quadrant, estimated_roi_months,
                estimated_annual_savings_usd, ceo_priority, overlooked_opportunity,
                data_support_score, confidence_score, needs_review,
                extraction_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            business_unit,
            candidate.get("department"),
            candidate.get("name", ""),
            candidate.get("process", ""),
            candidate.get("trigger_event", ""),
            candidate.get("action", ""),
            candidate.get("output", ""),
            candidate.get("owner", ""),
            candidate.get("complexity", "Medium"),
            candidate.get("impact", "Medium"),
            candidate.get("effort_estimate"),
            json_serialize(candidate.get("systems_involved", [])),
            candidate.get("current_manual_process_description", ""),
            json_serialize(candidate.get("data_sources_needed", [])),
            1 if candidate.get("approval_required") else 0,
            candidate.get("approval_threshold_usd"),
            json_serialize(candidate.get("monitoring_metrics", [])),
            candidate.get("effort_score", 3),
            candidate.get("impact_score", 3),
            candidate.get("priority_quadrant", "Incremental"),
            candidate.get("estimated_roi_months"),
            candidate.get("estimated_annual_savings_usd"),
            1 if candidate.get("ceo_priority") else 0,
            1 if candidate.get("overlooked_opportunity") else 0,
            candidate.get("data_support_score"),
            candidate.get("confidence_score", 0.0),
            1 if candidate.get("confidence_score", 1.0) < 0.7 else 0,
            candidate.get("extraction_source", "")
        ))
        
        self.conn.commit()

    def insert_team_structure(self, interview_id: int, company: str, business_unit: str, team: Dict):
        """Insert a team structure entity"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO team_structures (
                interview_id, company_name, business_unit, department,
                role, team_size, reports_to, coordinates_with,
                external_dependencies, confidence_score, needs_review, extraction_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            business_unit,
            team.get("department", "Unknown"),
            team.get("role", ""),
            team.get("team_size"),
            team.get("reports_to", ""),
            team.get("coordinates_with", ""),
            team.get("external_dependencies", ""),
            team.get("confidence_score", 0.0),
            1 if team.get("confidence_score", 1.0) < 0.7 else 0,
            team.get("extraction_source", "")
        ))
        
        self.conn.commit()

    def insert_knowledge_gap(self, interview_id: int, company: str, business_unit: str, gap: Dict):
        """Insert a knowledge gap entity"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO knowledge_gaps (
                interview_id, company_name, business_unit, department,
                area, affected_roles, impact, training_needed,
                confidence_score, needs_review, extraction_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            business_unit,
            gap.get("department", "Unknown"),
            gap.get("area", ""),
            gap.get("affected_roles", ""),
            gap.get("impact", ""),
            gap.get("training_needed", ""),
            gap.get("confidence_score", 0.0),
            1 if gap.get("confidence_score", 1.0) < 0.7 else 0,
            gap.get("extraction_source", "")
        ))
        
        self.conn.commit()

    def insert_success_pattern(self, interview_id: int, company: str, business_unit: str, pattern: Dict):
        """Insert a success pattern entity"""
        cursor = self.conn.cursor()
        
        # Handle replicable_to - might be list or string
        replicable_to = pattern.get("replicable_to", "")
        if isinstance(replicable_to, list):
            replicable_to = ", ".join(replicable_to)
        
        cursor.execute("""
            INSERT INTO success_patterns (
                interview_id, company_name, business_unit, department,
                pattern, role, benefit, replicable_to,
                confidence_score, needs_review, extraction_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            business_unit,
            pattern.get("department", "Unknown"),
            pattern.get("pattern", ""),
            pattern.get("role", ""),
            pattern.get("benefit", ""),
            str(replicable_to),
            pattern.get("confidence_score", 0.0),
            1 if pattern.get("confidence_score", 1.0) < 0.7 else 0,
            pattern.get("extraction_source", "")
        ))
        
        self.conn.commit()

    def insert_budget_constraint(self, interview_id: int, company: str, business_unit: str, constraint: Dict):
        """Insert a budget constraint entity"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO budget_constraints (
                interview_id, company_name, business_unit, department,
                area, budget_type, approval_required_above, approver, pain_point,
                confidence_score, needs_review, extraction_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            business_unit,
            constraint.get("department", "Unknown"),
            constraint.get("area", ""),
            constraint.get("budget_type", ""),
            constraint.get("approval_required_above"),
            constraint.get("approver", ""),
            constraint.get("pain_point", ""),
            constraint.get("confidence_score", 0.0),
            1 if constraint.get("confidence_score", 1.0) < 0.7 else 0,
            constraint.get("extraction_source", "")
        ))
        
        self.conn.commit()

    def insert_external_dependency(self, interview_id: int, company: str, business_unit: str, dependency: Dict):
        """Insert an external dependency entity"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO external_dependencies (
                interview_id, company_name, business_unit, department,
                vendor, service, frequency, coordinator, sla, payment_process,
                confidence_score, needs_review, extraction_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            company,
            business_unit,
            dependency.get("department", "Unknown"),
            dependency.get("vendor", ""),
            dependency.get("service", ""),
            dependency.get("frequency", ""),
            dependency.get("coordinator", ""),
            dependency.get("sla", ""),
            dependency.get("payment_process", ""),
            dependency.get("confidence_score", 0.0),
            1 if dependency.get("confidence_score", 1.0) < 0.7 else 0,
            dependency.get("extraction_source", "")
        ))
        
        self.conn.commit()

    def insert_enhanced_system(self, interview_id: int, company: str, business_unit: str, system: Dict):
        """Insert or update an enhanced system entity"""
        # For systems, we use insert_or_update_enhanced_system
        self.insert_or_update_enhanced_system(system, company)
    
    # ========================================================================
    # Consolidation Methods (Task 8)
    # ========================================================================
    
    def get_entities_by_type(
        self,
        entity_type: str,
        limit: Optional[int] = None,
        only_consolidated: bool = False
    ) -> List[Dict]:
        """
        Get entities of a specific type for duplicate detection
        
        Args:
            entity_type: Type of entity (systems, pain_points, etc.)
            limit: Optional limit on number of entities
            only_consolidated: If True, only return consolidated entities
            
        Returns:
            List of entity dicts
        """
        cursor = self.conn.cursor()
        
        # Build query
        query = f"SELECT * FROM {entity_type}"
        
        if only_consolidated:
            query += " WHERE is_consolidated = 1"
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            entities = []
            for row in rows:
                entity = dict(row)
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            print(f"  ⚠️  Error fetching entities: {e}")
            return []
    
    def update_consolidated_entity(
        self,
        entity_type: str,
        entity_id: int,
        updated_data: Dict,
        interview_id: int
    ) -> bool:
        """
        Update a consolidated entity with new data from another interview
        
        Args:
            entity_type: Type of entity
            entity_id: ID of entity to update
            updated_data: Dict with updated fields
            interview_id: Source interview ID
            
        Returns:
            True if successful, False otherwise
        """
        cursor = self.conn.cursor()
        
        try:
            # Build UPDATE statement dynamically
            set_clauses = []
            values = []
            
            for key, value in updated_data.items():
                # Skip id field
                if key == "id":
                    continue
                
                set_clauses.append(f"{key} = ?")
                
                # Handle JSON serialization
                if isinstance(value, (list, dict)):
                    values.append(json_serialize(value))
                else:
                    values.append(value)
            
            if not set_clauses:
                return True  # Nothing to update
            
            # Add entity_id to values
            values.append(entity_id)
            
            # Execute update
            query = f"""
                UPDATE {entity_type}
                SET {', '.join(set_clauses)}
                WHERE id = ?
            """
            
            cursor.execute(query, values)
            self.conn.commit()
            
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error updating consolidated entity: {e}")
            return False
    
    def insert_relationship(self, relationship: Dict) -> bool:
        """
        Insert a relationship between entities
        
        Args:
            relationship: Dict with relationship data
            
        Returns:
            True if successful, False otherwise
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO relationships (
                    source_entity_id,
                    source_entity_type,
                    relationship_type,
                    target_entity_id,
                    target_entity_type,
                    strength,
                    mentioned_in_interviews,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                relationship.get("source_entity_id"),
                relationship.get("source_entity_type"),
                relationship.get("relationship_type"),
                relationship.get("target_entity_id"),
                relationship.get("target_entity_type"),
                relationship.get("strength", 0.8),
                json_serialize(relationship.get("mentioned_in_interviews", [])),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error inserting relationship: {e}")
            return False
    
    def insert_consolidation_audit(self, audit_record: Dict) -> bool:
        """
        Insert a consolidation audit record
        
        Args:
            audit_record: Dict with audit data
            
        Returns:
            True if successful, False otherwise
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO consolidation_audit (
                    entity_type,
                    merged_entity_ids,
                    resulting_entity_id,
                    similarity_score,
                    consolidation_timestamp
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                audit_record.get("entity_type"),
                json_serialize(audit_record.get("merged_entity_ids", [])),
                audit_record.get("resulting_entity_id"),
                audit_record.get("similarity_score"),
                datetime.now().isoformat()
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"  ⚠️  Error inserting audit record: {e}")
            return False
    
    def check_entity_exists(
        self,
        entity_type: str,
        entity_id: int
    ) -> bool:
        """
        Check if an entity exists in the database
        
        Args:
            entity_type: Type of entity
            entity_id: ID of entity
            
        Returns:
            True if exists, False otherwise
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute(
                f"SELECT id FROM {entity_type} WHERE id = ?",
                (entity_id,)
            )
            return cursor.fetchone() is not None
            
        except Exception as e:
            print(f"  ⚠️  Error checking entity existence: {e}")
            return False
    
    def insert_or_update_entity(
        self,
        entity_type: str,
        entity: Dict,
        interview_id: int
    ) -> int:
        """
        Insert new entity or update existing consolidated entity
        
        This is the main entry point for consolidation-aware storage.
        Checks if entity is a duplicate and either:
        - Updates existing consolidated entity
        - Inserts new entity
        
        Args:
            entity_type: Type of entity
            entity: Entity data
            interview_id: Source interview ID
            
        Returns:
            Entity ID (new or existing)
        """
        # Check if this entity has been marked for consolidation
        if entity.get("is_consolidated") and entity.get("id"):
            # Update existing consolidated entity
            success = self.update_consolidated_entity(
                entity_type,
                entity["id"],
                entity,
                interview_id
            )
            return entity["id"] if success else None
        
        # Otherwise, insert as new entity
        # Use existing insert methods based on entity type
        # This will be called by the consolidation agent
        return None  # Handled by specific insert methods
