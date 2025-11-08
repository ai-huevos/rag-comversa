"""
Quality validation for extracted entities
Validates required fields, descriptions, and encoding
"""
import re
from typing import Dict, List, Tuple, Any


# Required fields per entity type
REQUIRED_FIELDS = {
    # v1.0 entities
    "pain_point": ["type", "description", "severity", "frequency"],
    "process": ["name", "owner", "domain", "description"],
    "system": ["name", "type"],
    "kpi": ["name", "definition", "owner"],
    "automation_candidate": ["name", "process", "complexity", "impact"],
    "inefficiency": ["description", "category", "frequency"],

    # v2.0 entities
    "communication_channel": ["channel_name", "purpose"],
    "decision_point": ["decision_type", "decision_maker"],
    "data_flow": ["source_system", "destination_system", "data_type"],
    "temporal_pattern": ["pattern_type", "frequency"],
    "failure_mode": ["failure_type", "description"],
    "team_structure": ["team_name", "team_size"],
    "knowledge_gap": ["gap_type", "description"],
    "success_pattern": ["pattern_type", "description"],
    "budget_constraint": ["constraint_type", "description"],
    "external_dependency": ["dependency_type", "provider"]
}

# Fields that should have minimum length
DESCRIPTION_FIELDS = ["description", "definition", "impact_description", "purpose"]

# Placeholder values to reject
PLACEHOLDER_VALUES = [
    "unknown", "n/a", "tbd", "to be determined", "not available",
    "no data", "none", "null", "undefined", "no especificado",
    "desconocido", "por determinar", "sin información"
]

# Minimum description length
MIN_DESCRIPTION_LENGTH = 20


class ValidationResult:
    """Result of entity validation"""

    def __init__(self, is_valid: bool, entity_type: str, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.entity_type = entity_type
        self.errors = errors or []
        self.warnings = warnings or []

    def __repr__(self):
        status = "✓ VALID" if self.is_valid else "✗ INVALID"
        return f"<ValidationResult {status} ({len(self.errors)} errors, {len(self.warnings)} warnings)>"


def validate_entity(entity: Dict, entity_type: str) -> ValidationResult:
    """
    Validate a single entity for quality issues

    Args:
        entity: Entity dictionary
        entity_type: Type of entity (e.g., "pain_point", "process")

    Returns:
        ValidationResult with errors and warnings
    """
    errors = []
    warnings = []

    # 1. Check required fields are populated
    required = REQUIRED_FIELDS.get(entity_type, [])
    for field in required:
        if field not in entity:
            errors.append(f"Missing required field: {field}")
        elif not entity[field] or str(entity[field]).strip() == "":
            errors.append(f"Required field is empty: {field}")

    # 2. Check description length
    for field in DESCRIPTION_FIELDS:
        if field in entity and entity[field]:
            value = str(entity[field]).strip()
            if len(value) < MIN_DESCRIPTION_LENGTH:
                warnings.append(f"Field '{field}' too short ({len(value)} chars, min {MIN_DESCRIPTION_LENGTH}): {value[:30]}...")

    # 3. Check for placeholder values
    for field, value in entity.items():
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in PLACEHOLDER_VALUES:
                errors.append(f"Placeholder value in '{field}': {value}")

    # 4. Check for encoding issues
    for field, value in entity.items():
        if isinstance(value, str):
            # Check for escape sequences
            if "\\" in value and ("\\n" in value or "\\t" in value or "\\x" in value):
                warnings.append(f"Possible encoding issue in '{field}': contains escape sequences")

            # Check for mojibake (common encoding issue patterns)
            if re.search(r'Ã¡|Ã©|Ã­|Ã³|Ãº', value):
                errors.append(f"Encoding issue in '{field}': mojibake detected")

    # Determine if valid (no errors, warnings are acceptable)
    is_valid = len(errors) == 0

    return ValidationResult(is_valid, entity_type, errors, warnings)


def validate_entities(entities: List[Dict], entity_type: str) -> Tuple[List[Dict], List[ValidationResult]]:
    """
    Validate multiple entities and return valid ones with results

    Args:
        entities: List of entity dictionaries
        entity_type: Type of entities

    Returns:
        Tuple of (valid_entities, all_validation_results)
    """
    valid_entities = []
    all_results = []

    for entity in entities:
        result = validate_entity(entity, entity_type)
        all_results.append(result)

        if result.is_valid:
            valid_entities.append(entity)
        else:
            # Flag entity as needing review
            entity["_validation_failed"] = True
            entity["_validation_errors"] = result.errors
            # Still include it but marked for review
            valid_entities.append(entity)

    return valid_entities, all_results


def get_validation_summary(results: List[ValidationResult]) -> Dict[str, Any]:
    """
    Generate summary statistics from validation results

    Args:
        results: List of ValidationResult objects

    Returns:
        Dictionary with summary statistics
    """
    total = len(results)
    valid = sum(1 for r in results if r.is_valid)
    invalid = total - valid

    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)

    # Group errors by type
    error_counts = {}
    for result in results:
        for error in result.errors:
            # Extract error type (first part before colon)
            error_type = error.split(":")[0] if ":" in error else error
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

    return {
        "total_entities": total,
        "valid_entities": valid,
        "invalid_entities": invalid,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "validity_rate": (valid / total * 100) if total > 0 else 0,
        "error_counts": error_counts
    }


def print_validation_summary(results: List[ValidationResult], entity_type: str = None):
    """Print human-readable validation summary"""
    summary = get_validation_summary(results)

    entity_label = f"{entity_type} " if entity_type else ""
    print(f"\n📊 Validation Summary - {entity_label}Entities")
    print(f"{'='*60}")
    print(f"Total: {summary['total_entities']}")
    print(f"Valid: {summary['valid_entities']} ({summary['validity_rate']:.1f}%)")
    print(f"Invalid: {summary['invalid_entities']}")
    print(f"Errors: {summary['total_errors']}")
    print(f"Warnings: {summary['total_warnings']}")

    if summary['error_counts']:
        print(f"\nTop Error Types:")
        for error_type, count in sorted(summary['error_counts'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {error_type}: {count}")


# Convenience function for validating all entity types from extraction
def validate_extraction_results(entities: Dict[str, List[Dict]]) -> Dict[str, List[ValidationResult]]:
    """
    Validate all entity types from extraction results

    Args:
        entities: Dictionary mapping entity type to list of entities

    Returns:
        Dictionary mapping entity type to validation results
    """
    all_results = {}

    # Map extraction keys to validation entity types
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
        "external_dependencies": "external_dependency",
        "pain_points_v2": "pain_point",
        "systems_v2": "system",
        "automation_candidates_v2": "automation_candidate"
    }

    for extraction_key, entity_list in entities.items():
        if extraction_key in entity_type_mapping:
            entity_type = entity_type_mapping[extraction_key]
            _, results = validate_entities(entity_list, entity_type)
            all_results[extraction_key] = results

    return all_results
