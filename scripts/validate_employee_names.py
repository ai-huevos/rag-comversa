#!/usr/bin/env python3
"""
Validation script for cleaned employee names.

Checks for potential issues and generates a review report.
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple


def validate_names(cleaned_file: Path) -> Dict:
    """
    Validate cleaned employee data and generate report.

    Returns:
        Dictionary with validation results
    """
    results = {
        'total': 0,
        'empty_fname': [],
        'empty_lname': [],
        'single_word_names': [],
        'very_long_names': [],
        'company_stats': defaultdict(lambda: {'count': 0, 'avg_fname_words': 0, 'avg_lname_words': 0}),
        'suspicious_cases': [],
        'gc_profile_coverage': {'with_profile': 0, 'without_profile': 0}
    }

    with open(cleaned_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        fname_words = defaultdict(list)
        lname_words = defaultdict(list)

        for row in reader:
            results['total'] += 1

            fname = row.get('fname', '').strip()
            lname = row.get('lname', '').strip()
            company = row.get('Empresa', '').strip()
            cargo = row.get('Cargo', '').strip()
            gc_profile = row.get('Perfil_Hipotetico_GC_Index', '').strip()

            # Check for empty fields
            if not fname:
                results['empty_fname'].append({
                    'lname': lname,
                    'company': company,
                    'cargo': cargo
                })

            if not lname:
                results['empty_lname'].append({
                    'fname': fname,
                    'company': company,
                    'cargo': cargo
                })

            # Check for single-word names (might be parsing issue)
            fname_parts = fname.split()
            lname_parts = lname.split()

            if len(fname_parts) == 1 and len(lname_parts) == 1:
                results['single_word_names'].append({
                    'fname': fname,
                    'lname': lname,
                    'company': company,
                    'cargo': cargo
                })

            # Check for very long names (might be parsing issue)
            if len(fname_parts) > 3 or len(lname_parts) > 3:
                results['very_long_names'].append({
                    'fname': fname,
                    'lname': lname,
                    'company': company,
                    'cargo': cargo,
                    'fname_words': len(fname_parts),
                    'lname_words': len(lname_parts)
                })

            # Company statistics
            if company:
                results['company_stats'][company]['count'] += 1
                fname_words[company].append(len(fname_parts))
                lname_words[company].append(len(lname_parts))

            # GC Profile coverage
            if gc_profile:
                results['gc_profile_coverage']['with_profile'] += 1
            else:
                results['gc_profile_coverage']['without_profile'] += 1

            # Suspicious cases (heuristics)
            suspicious = []

            # Check if first name looks like a last name (all caps, compound)
            if fname and fname.isupper():
                suspicious.append("First name is all caps")

            # Check if last name looks like a first name (single lowercase word)
            if lname and len(lname_parts) == 1 and lname[0].islower():
                suspicious.append("Last name might be first name")

            # Check for potential company convention violations
            if company == "LOS TAJIBOS":
                # LOS TAJIBOS should have 1-2 last names (2-4 words total in last name)
                if len(lname_parts) > 4:
                    suspicious.append(f"LOS TAJIBOS: Too many last name words ({len(lname_parts)})")
            else:
                # COMVERSA/BOLIVIAN FOODS should have simpler last names
                if len(lname_parts) > 3:
                    suspicious.append(f"{company}: Unusually long last name ({len(lname_parts)} words)")

            if suspicious:
                results['suspicious_cases'].append({
                    'fname': fname,
                    'lname': lname,
                    'company': company,
                    'cargo': cargo,
                    'issues': suspicious
                })

        # Calculate averages
        for company, data in results['company_stats'].items():
            if data['count'] > 0:
                data['avg_fname_words'] = sum(fname_words[company]) / data['count']
                data['avg_lname_words'] = sum(lname_words[company]) / data['count']

    return results


def print_validation_report(results: Dict) -> None:
    """Print human-readable validation report."""
    print("\n" + "="*70)
    print("📋 EMPLOYEE NAME VALIDATION REPORT")
    print("="*70)

    print(f"\n📊 Total employees processed: {results['total']}")

    # GC Profile coverage
    print(f"\n🎯 GC Profile Coverage:")
    print(f"   ✅ With profile: {results['gc_profile_coverage']['with_profile']}")
    print(f"   ⚠️  Without profile: {results['gc_profile_coverage']['without_profile']}")

    # Company statistics
    print(f"\n🏢 Statistics by Company:")
    for company, stats in results['company_stats'].items():
        print(f"\n   {company}:")
        print(f"      Employees: {stats['count']}")
        print(f"      Avg first name words: {stats['avg_fname_words']:.1f}")
        print(f"      Avg last name words: {stats['avg_lname_words']:.1f}")

    # Empty fields
    if results['empty_fname']:
        print(f"\n❌ Empty first names ({len(results['empty_fname'])}):")
        for item in results['empty_fname']:
            print(f"   - {item['lname']} ({item['company']}, {item['cargo']})")

    if results['empty_lname']:
        print(f"\n❌ Empty last names ({len(results['empty_lname'])}):")
        for item in results['empty_lname']:
            print(f"   - {item['fname']} ({item['company']}, {item['cargo']})")

    # Single-word names
    if results['single_word_names']:
        print(f"\n⚠️  Single-word names ({len(results['single_word_names'])}):")
        print("   (These might be correct, but worth reviewing)")
        for item in results['single_word_names']:
            print(f"   - {item['fname']} {item['lname']} ({item['company']}, {item['cargo']})")

    # Very long names
    if results['very_long_names']:
        print(f"\n⚠️  Very long names ({len(results['very_long_names'])}):")
        for item in results['very_long_names']:
            print(f"   - {item['fname']} | {item['lname']}")
            print(f"     ({item['fname_words']} fname words, {item['lname_words']} lname words)")
            print(f"     Company: {item['company']}, Role: {item['cargo']}")

    # Suspicious cases
    if results['suspicious_cases']:
        print(f"\n⚠️  Suspicious cases requiring manual review ({len(results['suspicious_cases'])}):")
        for item in results['suspicious_cases']:
            print(f"\n   - {item['fname']} | {item['lname']}")
            print(f"     Company: {item['company']}, Role: {item['cargo']}")
            print(f"     Issues: {', '.join(item['issues'])}")

    # Summary
    print("\n" + "="*70)
    issues_count = (len(results['empty_fname']) +
                   len(results['empty_lname']) +
                   len(results['suspicious_cases']))

    if issues_count == 0:
        print("✅ All validations passed! No issues detected.")
    else:
        print(f"⚠️  Found {issues_count} potential issues requiring review.")
        print("   Review the cases above and verify against source data.")

    print("\n💡 Recommendations:")
    print("   1. Manually verify suspicious cases")
    print("   2. Cross-check with HR records if available")
    print("   3. Update source data if corrections needed")
    print("   4. Re-run cleaning script after source corrections")
    print("="*70 + "\n")


def main():
    """Main entry point."""
    base_dir = Path(__file__).parent.parent
    cleaned_file = base_dir / 'data' / 'company_info' / 'Complete Reports' / 'perfiles_gc_index_completo_44_empleados_cleaned.csv'

    if not cleaned_file.exists():
        print(f"❌ Error: Cleaned file not found: {cleaned_file}")
        print("   Run clean_employee_names.py first.")
        sys.exit(1)

    print("🔍 Validating cleaned employee names...")
    results = validate_names(cleaned_file)
    print_validation_report(results)


if __name__ == '__main__':
    main()
