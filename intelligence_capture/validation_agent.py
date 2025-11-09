"""
ValidationAgent - Multi-agent validation workflow
Checks completeness and quality of extracted entities
Supports rule-based and optional LLM-based validation
"""
import os
from typing import Dict, List, Tuple, Any, Optional
from .validation import validate_entity, ValidationResult
import openai


# Entity type keywords for heuristic completeness checking
ENTITY_KEYWORDS = {
    "pain_points": ["pain", "problem", "issue", "challenge", "difficulty", "frustration", "struggle"],
    "processes": ["process", "workflow", "procedure", "steps", "how we", "how they"],
    "systems": ["system", "tool", "software", "platform", "application", "database"],
    "kpis": ["metric", "kpi", "measure", "track", "monitor", "performance indicator"],
    "automation_candidates": ["automate", "automation", "manual", "repetitive", "automated"],
    "inefficiencies": ["inefficient", "waste", "slow", "delay", "bottleneck", "redundant"],
    "communication_channels": ["communicate", "communication", "meeting", "email", "slack", "teams"],
    "decision_points": ["decision", "approve", "approval", "decide", "choice"],
    "data_flows": ["data", "transfer", "export", "import", "flow", "integration"],
    "temporal_patterns": ["daily", "weekly", "monthly", "quarterly", "seasonal", "periodic"],
    "failure_modes": ["fail", "failure", "error", "crash", "downtime", "outage"],
    "team_structures": ["team", "department", "group", "organization", "reports to"],
    "knowledge_gaps": ["don't know", "unclear", "uncertain", "not sure", "learning"],
    "success_patterns": ["success", "working well", "effective", "best practice", "achievement"],
    "budget_constraints": ["budget", "cost", "expense", "funding", "financial"],
    "external_dependencies": ["vendor", "third party", "external", "supplier", "partner"]
}


# Critical entity types that should almost always have data
CRITICAL_ENTITY_TYPES = ["pain_points", "processes", "systems"]


class CompletenessResult:
    """Result of completeness validation"""

    def __init__(self, entity_type: str, is_complete: bool, reason: str = None):
        self.entity_type = entity_type
        self.is_complete = is_complete
        self.reason = reason or ("Complete" if is_complete else "Incomplete")

    def __repr__(self):
        status = "✓" if self.is_complete else "✗"
        return f"<CompletenessResult {status} {self.entity_type}: {self.reason}>"


class ValidationAgent:
    """
    Multi-agent validation workflow for extracted entities
    Checks completeness, quality, and suggests re-extraction
    """

    def __init__(self, enable_llm_validation: bool = False, openai_api_key: str = None):
        """
        Initialize validation agent

        Args:
            enable_llm_validation: Enable LLM-based completeness checking (costs tokens)
            openai_api_key: OpenAI API key for LLM validation (optional)
        """
        self.enable_llm_validation = enable_llm_validation

        if enable_llm_validation and openai_api_key:
            openai.api_key = openai_api_key

    def validate_entities(
        self,
        entities: Dict[str, List[Dict]],
        qa_pairs: Dict[str, str],
        meta: Dict = None
    ) -> Tuple[Dict[str, List[str]], Dict[str, CompletenessResult]]:
        """
        Validate extracted entities for completeness and quality

        Args:
            entities: Dictionary of extracted entities
            qa_pairs: Interview Q&A pairs for context
            meta: Interview metadata

        Returns:
            Tuple of (missing_entity_types, completeness_results)
        """
        missing_entity_types = []
        completeness_results = {}

        # Run rule-based validation
        rule_based_results = self._validate_completeness_rule_based(entities, qa_pairs)
        completeness_results.update(rule_based_results)

        # Identify missing critical entities
        for entity_type in CRITICAL_ENTITY_TYPES:
            if entity_type not in entities or len(entities[entity_type]) == 0:
                result = completeness_results.get(entity_type)
                if result and not result.is_complete:
                    missing_entity_types.append(entity_type)

        # Run optional LLM validation for critical types
        if self.enable_llm_validation:
            llm_results = self._validate_completeness_llm(entities, qa_pairs, CRITICAL_ENTITY_TYPES)

            # Override rule-based results with LLM results
            for entity_type, result in llm_results.items():
                completeness_results[entity_type] = result
                if not result.is_complete and entity_type not in missing_entity_types:
                    missing_entity_types.append(entity_type)

        return missing_entity_types, completeness_results

    def _validate_completeness_rule_based(
        self,
        entities: Dict[str, List[Dict]],
        qa_pairs: Dict[str, str]
    ) -> Dict[str, CompletenessResult]:
        """
        Rule-based heuristic for checking entity completeness
        Checks if interview mentions keywords but no entities extracted

        Args:
            entities: Extracted entities
            qa_pairs: Interview Q&A pairs

        Returns:
            Dictionary of CompletenessResult per entity type
        """
        results = {}

        # Combine all interview text for keyword search
        interview_text = " ".join(qa_pairs.values()).lower()

        for entity_type, keywords in ENTITY_KEYWORDS.items():
            # Check if entities were extracted
            entity_count = len(entities.get(entity_type, []))

            # Check if keywords appear in interview
            keyword_matches = sum(1 for keyword in keywords if keyword in interview_text)

            # Heuristic: If 2+ keywords mentioned but 0 entities, likely incomplete
            if keyword_matches >= 2 and entity_count == 0:
                results[entity_type] = CompletenessResult(
                    entity_type,
                    is_complete=False,
                    reason=f"Keywords found ({keyword_matches}) but no entities extracted"
                )
            else:
                results[entity_type] = CompletenessResult(
                    entity_type,
                    is_complete=True,
                    reason=f"Extracted {entity_count} entities"
                )

        return results

    def _validate_completeness_llm(
        self,
        entities: Dict[str, List[Dict]],
        qa_pairs: Dict[str, str],
        entity_types: List[str]
    ) -> Dict[str, CompletenessResult]:
        """
        LLM-based completeness validation for critical entity types
        Uses lightweight prompt to check if entities are missing

        Args:
            entities: Extracted entities
            qa_pairs: Interview Q&A pairs
            entity_types: List of entity types to validate

        Returns:
            Dictionary of CompletenessResult per entity type
        """
        results = {}

        # Combine interview text
        interview_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])

        for entity_type in entity_types:
            entity_count = len(entities.get(entity_type, []))

            # Only validate if no entities were extracted
            if entity_count > 0:
                results[entity_type] = CompletenessResult(
                    entity_type,
                    is_complete=True,
                    reason=f"Extracted {entity_count} entities"
                )
                continue

            # Create lightweight validation prompt
            prompt = self._create_completeness_prompt(entity_type, interview_text)

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",  # Use cheaper model for validation
                    messages=[
                        {"role": "system", "content": "You are a validation assistant. Answer with YES or NO only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                    max_tokens=10
                )

                answer = response.choices[0].message.content.strip().upper()

                if "YES" in answer:
                    results[entity_type] = CompletenessResult(
                        entity_type,
                        is_complete=False,
                        reason="LLM detected missing entities"
                    )
                else:
                    results[entity_type] = CompletenessResult(
                        entity_type,
                        is_complete=True,
                        reason="LLM confirmed no entities present"
                    )

            except Exception as e:
                # Fall back to rule-based on error
                results[entity_type] = CompletenessResult(
                    entity_type,
                    is_complete=True,
                    reason=f"LLM validation failed: {str(e)[:50]}"
                )

        return results

    def _create_completeness_prompt(self, entity_type: str, interview_text: str) -> str:
        """Create prompt for LLM completeness validation"""

        entity_descriptions = {
            "pain_points": "problems, challenges, frustrations, or difficulties mentioned",
            "processes": "workflows, procedures, or step-by-step processes described",
            "systems": "software tools, systems, platforms, or applications mentioned"
        }

        description = entity_descriptions.get(entity_type, entity_type)

        # Truncate interview to fit in context (roughly 2000 tokens)
        max_chars = 8000
        if len(interview_text) > max_chars:
            interview_text = interview_text[:max_chars] + "\n... (truncated)"

        return f"""Based on the following interview, are there any {description}?

Interview:
{interview_text}

Answer YES if there are {description} mentioned in the interview, NO if there are none.
Answer with YES or NO only."""

    def validate_quality(self, entities: Dict[str, List[Dict]]) -> Dict[str, List[ValidationResult]]:
        """
        Validate quality of all extracted entities
        Uses existing validation module

        Args:
            entities: Dictionary of extracted entities

        Returns:
            Dictionary mapping entity type to list of ValidationResult
        """
        from .validation import validate_entities

        all_results = {}

        entity_type_mapping = {
            "pain_points": "pain_point",
            "processes": "process",
            "systems": "system",
            "kpis": "kpi",
            "automation_candidates": "automation_candidate",
            "inefficiencies": "inefficiency",
            "communication_channels": "communication_channel",
            "decision_points": "decision_point",
            "data_flows": "data_flow",
            "temporal_patterns": "temporal_pattern",
            "failure_modes": "failure_mode",
            "team_structures": "team_structure",
            "knowledge_gaps": "knowledge_gap",
            "success_patterns": "success_pattern",
            "budget_constraints": "budget_constraint",
            "external_dependencies": "external_dependency"
        }

        for extraction_key, entity_list in entities.items():
            if extraction_key in entity_type_mapping and entity_list:
                entity_type = entity_type_mapping[extraction_key]
                _, results = validate_entities(entity_list, entity_type)
                all_results[extraction_key] = results

        return all_results

    def get_validation_summary(
        self,
        completeness_results: Dict[str, CompletenessResult],
        quality_results: Dict[str, List[ValidationResult]]
    ) -> Dict[str, Any]:
        """
        Generate summary of validation results

        Args:
            completeness_results: Completeness validation results
            quality_results: Quality validation results

        Returns:
            Summary dictionary
        """
        summary = {
            "completeness": {
                "total_types": len(completeness_results),
                "complete_types": sum(1 for r in completeness_results.values() if r.is_complete),
                "incomplete_types": sum(1 for r in completeness_results.values() if not r.is_complete),
                "incomplete_list": [r.entity_type for r in completeness_results.values() if not r.is_complete]
            },
            "quality": {
                "total_entities": sum(len(results) for results in quality_results.values()),
                "valid_entities": sum(sum(1 for r in results if r.is_valid) for results in quality_results.values()),
                "invalid_entities": sum(sum(1 for r in results if not r.is_valid) for results in quality_results.values()),
                "total_errors": sum(sum(len(r.errors) for r in results) for results in quality_results.values()),
                "total_warnings": sum(sum(len(r.warnings) for r in results) for results in quality_results.values())
            }
        }

        return summary

    def validate_consistency(self, entities: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
        """
        Validate consistency across entity relationships
        Checks if entity references point to existing entities

        Args:
            entities: Dictionary of extracted entities

        Returns:
            List of consistency issues found
        """
        issues = []

        # Build lookup indexes for faster searching
        system_names = {s.get("name", "").lower() for s in entities.get("systems", [])}
        system_names.update({s.get("system_name", "").lower() for s in entities.get("systems_v2", [])})

        process_names = {p.get("name", "").lower() for p in entities.get("processes", [])}
        process_names.update({p.get("process_name", "").lower() for p in entities.get("processes_v2", [])})

        # Check 1: Pain points referencing non-existent systems
        for pain_point in entities.get("pain_points", []):
            related_systems = pain_point.get("related_systems", [])
            if isinstance(related_systems, list):
                for system_name in related_systems:
                    if system_name and system_name.lower() not in system_names:
                        issues.append({
                            "type": "missing_reference",
                            "entity_type": "pain_point",
                            "entity_name": pain_point.get("name", "Unknown"),
                            "issue": f"References non-existent system: {system_name}",
                            "severity": "warning"
                        })

        # Check 2: Automation candidates referencing non-existent processes
        for automation in entities.get("automation_candidates", []):
            process_name = automation.get("process_name", "")
            if process_name and process_name.lower() not in process_names:
                issues.append({
                    "type": "missing_reference",
                    "entity_type": "automation_candidate",
                    "entity_name": automation.get("name", "Unknown"),
                    "issue": f"References non-existent process: {process_name}",
                    "severity": "warning"
                })

        # Check 3: Data flows referencing non-existent systems
        for flow in entities.get("data_flows", []):
            source = flow.get("source_system", "")
            target = flow.get("target_system", "")

            if source and source.lower() not in system_names:
                issues.append({
                    "type": "missing_reference",
                    "entity_type": "data_flow",
                    "entity_name": flow.get("data_type", "Unknown flow"),
                    "issue": f"Source system not found: {source}",
                    "severity": "warning"
                })

            if target and target.lower() not in system_names:
                issues.append({
                    "type": "missing_reference",
                    "entity_type": "data_flow",
                    "entity_name": flow.get("data_type", "Unknown flow"),
                    "issue": f"Target system not found: {target}",
                    "severity": "warning"
                })

        return issues

    def detect_hallucinations(
        self,
        entities: Dict[str, List[Dict]],
        interview_text: str,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Detect potential hallucinations by checking if entity details
        have support in the source interview text

        Args:
            entities: Extracted entities
            interview_text: Original interview text
            threshold: Minimum keyword overlap ratio (0.0-1.0)

        Returns:
            List of potential hallucination issues
        """
        issues = []
        interview_lower = interview_text.lower()

        # Check critical entity types for hallucination
        critical_types = ["pain_points", "systems", "processes", "automation_candidates"]

        for entity_type in critical_types:
            for entity in entities.get(entity_type, []):
                name = entity.get("name", "")
                description = entity.get("description", "")

                if not name and not description:
                    continue

                # Extract keywords from entity (split and filter)
                keywords = []
                if name:
                    keywords.extend([w.strip().lower() for w in name.split() if len(w) > 3])
                if description:
                    keywords.extend([w.strip().lower() for w in description.split() if len(w) > 3])

                # Remove duplicates and common words
                common_words = {"the", "this", "that", "with", "from", "have", "been", "will", "what", "when", "where"}
                keywords = [k for k in set(keywords) if k not in common_words]

                if not keywords:
                    continue

                # Count how many keywords appear in interview
                matches = sum(1 for keyword in keywords if keyword in interview_lower)
                overlap_ratio = matches / len(keywords) if keywords else 0.0

                # Flag as potential hallucination if overlap is too low
                if overlap_ratio < threshold:
                    issues.append({
                        "type": "potential_hallucination",
                        "entity_type": entity_type,
                        "entity_name": name or "Unknown",
                        "issue": f"Low text support: {int(overlap_ratio*100)}% keywords found in interview",
                        "severity": "warning" if overlap_ratio > 0.2 else "error",
                        "overlap_ratio": overlap_ratio
                    })

        return issues

    def print_validation_report(
        self,
        completeness_results: Dict[str, CompletenessResult],
        quality_results: Dict[str, List[ValidationResult]],
        consistency_issues: List[Dict] = None,
        hallucination_issues: List[Dict] = None
    ):
        """Print human-readable validation report"""

        summary = self.get_validation_summary(completeness_results, quality_results)

        print(f"\n{'='*70}")
        print(f"📋 VALIDATION REPORT")
        print(f"{'='*70}")

        print(f"\n🔍 Completeness Check:")
        print(f"  Complete entity types: {summary['completeness']['complete_types']}/{summary['completeness']['total_types']}")
        print(f"  Incomplete entity types: {summary['completeness']['incomplete_types']}")

        if summary['completeness']['incomplete_list']:
            print(f"\n  Missing entities for:")
            for entity_type in summary['completeness']['incomplete_list']:
                result = completeness_results[entity_type]
                print(f"    - {entity_type}: {result.reason}")

        print(f"\n✅ Quality Check:")
        print(f"  Total entities: {summary['quality']['total_entities']}")
        print(f"  Valid: {summary['quality']['valid_entities']}")
        print(f"  Invalid: {summary['quality']['invalid_entities']}")
        print(f"  Errors: {summary['quality']['total_errors']}")
        print(f"  Warnings: {summary['quality']['total_warnings']}")

        if consistency_issues is not None:
            print(f"\n🔗 Consistency Check:")
            print(f"  Total issues: {len(consistency_issues)}")
            if consistency_issues:
                errors = [i for i in consistency_issues if i.get("severity") == "error"]
                warnings = [i for i in consistency_issues if i.get("severity") == "warning"]
                print(f"  Errors: {len(errors)}")
                print(f"  Warnings: {len(warnings)}")

                if errors:
                    print(f"\n  Critical consistency issues:")
                    for issue in errors[:5]:  # Show first 5
                        print(f"    - {issue['entity_type']}: {issue['issue']}")

        if hallucination_issues is not None:
            print(f"\n🎭 Hallucination Detection:")
            print(f"  Total potential hallucinations: {len(hallucination_issues)}")
            if hallucination_issues:
                errors = [i for i in hallucination_issues if i.get("severity") == "error"]
                warnings = [i for i in hallucination_issues if i.get("severity") == "warning"]
                print(f"  High confidence: {len(errors)}")
                print(f"  Low confidence: {len(warnings)}")

                if errors:
                    print(f"\n  High confidence hallucinations:")
                    for issue in errors[:3]:  # Show first 3
                        print(f"    - {issue['entity_type']}: {issue['entity_name']}")
                        print(f"      {issue['issue']}")

        print(f"\n{'='*70}")
