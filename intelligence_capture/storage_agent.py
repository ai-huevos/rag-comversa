"""
StorageAgent - Transactional database storage with rollback capability
Ensures atomicity and data integrity for multi-entity storage operations
"""
from typing import Dict, List, Any
from pathlib import Path


class StorageAgent:
    """
    Manages all database operations with transactions
    Ensures atomic storage with rollback on errors
    """

    def __init__(self, db):
        """
        Initialize storage agent with database connection

        Args:
            db: Database instance (IntelligenceDB or EnhancedIntelligenceDB)
        """
        self.db = db

    def store_all(
        self,
        entities: Dict[str, List[Dict]],
        interview_id: int,
        company: str,
        meta: Dict
    ) -> Dict[str, Any]:
        """
        Store all entities in a single transaction
        Rollback if any storage fails

        Args:
            entities: Dictionary of extracted entities
            interview_id: Interview ID
            company: Company name
            meta: Interview metadata

        Returns:
            Dictionary with success status, counts, and errors
        """
        result = {
            "success": False,
            "interview_id": interview_id,
            "entities_stored": 0,
            "entities_by_type": {},
            "errors": []
        }

        business_unit = meta.get("business_unit", meta.get("department", "Unknown"))

        # Begin transaction
        try:
            self.db.conn.execute("BEGIN TRANSACTION")

            # Store v1.0 entities
            v1_counts = self._store_v1_entities(entities, interview_id, company)
            result["entities_by_type"].update(v1_counts)

            # Store v2.0 entities
            v2_counts = self._store_v2_entities(entities, interview_id, company, business_unit)
            result["entities_by_type"].update(v2_counts)

            # Commit transaction
            self.db.conn.commit()

            result["success"] = True
            result["entities_stored"] = sum(result["entities_by_type"].values())

            print(f"     ✓ Stored {result['entities_stored']} entities across {len(result['entities_by_type'])} types")

        except Exception as e:
            # Rollback on error
            self.db.conn.rollback()
            error_msg = str(e)
            result["errors"].append(f"Transaction failed: {error_msg[:200]}")
            print(f"     ❌ Storage failed, rolled back: {error_msg[:100]}")

        return result

    def _store_v1_entities(
        self,
        entities: Dict[str, List[Dict]],
        interview_id: int,
        company: str
    ) -> Dict[str, int]:
        """
        Store v1.0 entities (original 6 types)

        Returns:
            Dictionary mapping entity type to count stored
        """
        counts = {}

        # Pain points
        pain_points = entities.get("pain_points", [])
        for pain_point in pain_points:
            self.db.insert_pain_point(interview_id, company, pain_point)
        counts["pain_points"] = len(pain_points)

        # Processes
        processes = entities.get("processes", [])
        for process in processes:
            self.db.insert_process(interview_id, company, process)
        counts["processes"] = len(processes)

        # Systems
        systems = entities.get("systems", [])
        for system in systems:
            self.db.insert_or_update_system(system, company)
        counts["systems"] = len(systems)

        # KPIs
        kpis = entities.get("kpis", [])
        for kpi in kpis:
            self.db.insert_kpi(interview_id, company, kpi)
        counts["kpis"] = len(kpis)

        # Automation candidates
        automations = entities.get("automation_candidates", [])
        for automation in automations:
            self.db.insert_automation_candidate(interview_id, company, automation)
        counts["automation_candidates"] = len(automations)

        # Inefficiencies
        inefficiencies = entities.get("inefficiencies", [])
        for inefficiency in inefficiencies:
            self.db.insert_inefficiency(interview_id, company, inefficiency)
        counts["inefficiencies"] = len(inefficiencies)

        return counts

    def _store_v2_entities(
        self,
        entities: Dict[str, List[Dict]],
        interview_id: int,
        company: str,
        business_unit: str
    ) -> Dict[str, int]:
        """
        Store v2.0 entities (11 new types)

        Returns:
            Dictionary mapping entity type to count stored
        """
        counts = {}

        # Communication channels
        channels = entities.get("communication_channels", [])
        for channel in channels:
            self.db.insert_communication_channel(interview_id, company, business_unit, channel)
        counts["communication_channels"] = len(channels)

        # Decision points
        decisions = entities.get("decision_points", [])
        for decision in decisions:
            self.db.insert_decision_point(interview_id, company, business_unit, decision)
        counts["decision_points"] = len(decisions)

        # Data flows
        flows = entities.get("data_flows", [])
        for flow in flows:
            self.db.insert_data_flow(interview_id, company, business_unit, flow)
        counts["data_flows"] = len(flows)

        # Temporal patterns
        patterns = entities.get("temporal_patterns", [])
        for pattern in patterns:
            self.db.insert_temporal_pattern(interview_id, company, business_unit, pattern)
        counts["temporal_patterns"] = len(patterns)

        # Failure modes
        failures = entities.get("failure_modes", [])
        for failure in failures:
            self.db.insert_failure_mode(interview_id, company, business_unit, failure)
        counts["failure_modes"] = len(failures)

        # Team structures
        teams = entities.get("team_structures", [])
        for team in teams:
            self.db.insert_team_structure(interview_id, company, business_unit, team)
        counts["team_structures"] = len(teams)

        # Knowledge gaps
        gaps = entities.get("knowledge_gaps", [])
        for gap in gaps:
            self.db.insert_knowledge_gap(interview_id, company, business_unit, gap)
        counts["knowledge_gaps"] = len(gaps)

        # Success patterns
        successes = entities.get("success_patterns", [])
        for success in successes:
            self.db.insert_success_pattern(interview_id, company, business_unit, success)
        counts["success_patterns"] = len(successes)

        # Budget constraints
        budgets = entities.get("budget_constraints", [])
        for budget in budgets:
            self.db.insert_budget_constraint(interview_id, company, business_unit, budget)
        counts["budget_constraints"] = len(budgets)

        # External dependencies
        dependencies = entities.get("external_dependencies", [])
        for dependency in dependencies:
            self.db.insert_external_dependency(interview_id, company, business_unit, dependency)
        counts["external_dependencies"] = len(dependencies)

        # Enhanced v1.0 entities (if present)
        enhanced_pain_points = entities.get("pain_points_v2", [])
        for pain_point in enhanced_pain_points:
            self.db.insert_enhanced_pain_point(interview_id, company, business_unit, pain_point)
        counts["enhanced_pain_points"] = len(enhanced_pain_points)

        enhanced_systems = entities.get("systems_v2", [])
        for system in enhanced_systems:
            self.db.insert_or_update_enhanced_system(system, company)
        counts["enhanced_systems"] = len(enhanced_systems)

        enhanced_automations = entities.get("automation_candidates_v2", [])
        for automation in enhanced_automations:
            self.db.insert_enhanced_automation_candidate(interview_id, company, business_unit, automation)
        counts["enhanced_automation_candidates"] = len(enhanced_automations)

        return counts

    def rollback_interview(self, interview_id: int) -> Dict[str, Any]:
        """
        Rollback all entities for a specific interview

        Args:
            interview_id: Interview ID to rollback

        Returns:
            Dictionary with success status and counts
        """
        result = {
            "success": False,
            "interview_id": interview_id,
            "entities_deleted": 0,
            "errors": []
        }

        try:
            self.db.conn.execute("BEGIN TRANSACTION")

            # Get entity counts before deletion
            cursor = self.db.conn.cursor()

            # Delete from all v1.0 tables
            v1_tables = ["pain_points", "processes", "kpis", "automation_candidates", "inefficiencies"]
            for table in v1_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE interview_id = ?", (interview_id,))
                count = cursor.fetchone()[0]
                cursor.execute(f"DELETE FROM {table} WHERE interview_id = ?", (interview_id,))
                result["entities_deleted"] += count

            # Delete from all v2.0 tables
            v2_tables = [
                "communication_channels", "decision_points", "data_flows",
                "temporal_patterns", "failure_modes", "team_structures",
                "knowledge_gaps", "success_patterns", "budget_constraints",
                "external_dependencies", "enhanced_pain_points"
            ]
            for table in v2_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE interview_id = ?", (interview_id,))
                    count = cursor.fetchone()[0]
                    cursor.execute(f"DELETE FROM {table} WHERE interview_id = ?", (interview_id,))
                    result["entities_deleted"] += count
                except Exception as e:
                    # Table might not exist, skip it
                    pass

            # Update interview status
            cursor.execute(
                "UPDATE interviews SET extraction_status = ? WHERE id = ?",
                ("rolled_back", interview_id)
            )

            # Commit transaction
            self.db.conn.commit()

            result["success"] = True
            print(f"✓ Rolled back interview {interview_id}: {result['entities_deleted']} entities deleted")

        except Exception as e:
            self.db.conn.rollback()
            error_msg = str(e)
            result["errors"].append(f"Rollback failed: {error_msg[:200]}")
            print(f"❌ Rollback failed: {error_msg[:100]}")

        return result

    def verify_storage(self, interview_id: int) -> Dict[str, Any]:
        """
        Verify that all entities were stored correctly

        Args:
            interview_id: Interview ID to verify

        Returns:
            Dictionary with verification results
        """
        cursor = self.db.conn.cursor()

        result = {
            "interview_exists": False,
            "entity_counts": {},
            "total_entities": 0,
            "missing_types": []
        }

        # Check if interview exists
        cursor.execute("SELECT COUNT(*) FROM interviews WHERE id = ?", (interview_id,))
        result["interview_exists"] = cursor.fetchone()[0] > 0

        if not result["interview_exists"]:
            return result

        # Count entities in each table
        all_tables = [
            "pain_points", "processes", "kpis", "automation_candidates", "inefficiencies",
            "communication_channels", "decision_points", "data_flows", "temporal_patterns",
            "failure_modes", "team_structures", "knowledge_gaps", "success_patterns",
            "budget_constraints", "external_dependencies"
        ]

        for table in all_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE interview_id = ?", (interview_id,))
                count = cursor.fetchone()[0]
                result["entity_counts"][table] = count
                result["total_entities"] += count

                if count == 0:
                    result["missing_types"].append(table)
            except Exception as e:
                result["entity_counts"][table] = f"Error: {str(e)[:50]}"

        return result
