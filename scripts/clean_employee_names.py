#!/usr/bin/env python3
"""
Smart name cleaning script for employee data.

Handles two naming conventions:
- LOS TAJIBOS: Last names first (1-2) + First names (1-2)
  Examples: "Mejia Mangudo Pamela Lucia", "Flores Javier"
- COMVERSA/BOLIVIAN FOODS: First names first + Last names
  Examples: "Gabriela Loza", "Samuel Doria Medina Auza"
"""

import csv
import sys
from pathlib import Path
from typing import Tuple, List
import re


class NameParser:
    """Semantic name parser that handles multiple naming conventions."""

    # Common Spanish compound last names (apellidos compuestos)
    COMPOUND_INDICATORS = {
        'de', 'del', 'de la', 'de los', 'de las',
        'van', 'von', 'mac', 'mc'
    }

    # Common Spanish first names for disambiguation
    COMMON_FIRST_NAMES = {
        # Male
        'juan', 'jose', 'carlos', 'luis', 'miguel', 'javier', 'diego', 'pablo',
        'pedro', 'antonio', 'fernando', 'roberto', 'manuel', 'francisco', 'daniel',
        'rafael', 'alejandro', 'ricardo', 'andres', 'eduardo', 'sergio', 'alberto',
        'oscar', 'jorge', 'raul', 'marco', 'enrique', 'guillermo', 'victor',
        'fabian', 'gonzalo', 'mauricio', 'alvaro', 'enzo', 'ezequiel', 'nicolas',
        'gabriel', 'alain', 'moises', 'danny', 'samuel', 'juvenal', 'gualberto',
        'pavel', 'josue',
        # Female
        'maria', 'ana', 'laura', 'carmen', 'patricia', 'rosa', 'sandra', 'monica',
        'adriana', 'beatriz', 'claudia', 'diana', 'elena', 'gabriela', 'isabel',
        'julia', 'lucia', 'mariana', 'natalia', 'paola', 'silvia', 'veronica',
        'camila', 'noemi', 'alejandra', 'carla', 'micaela', 'sissy', 'pamela',
        'ines', 'griselda', 'fridda', 'selva', 'araceli', 'antonieta', 'martha',
        'elizabeth', 'wendy', 'alicia', 'marcia', 'gaby', 'andrea', 'columba'
    }

    def __init__(self, company: str):
        self.company = company.upper().strip()

    def parse(self, full_name: str) -> Tuple[str, str]:
        """
        Parse full name into first name and last name based on company convention.

        Args:
            full_name: Complete name string

        Returns:
            Tuple of (first_name, last_name)
        """
        if not full_name or not full_name.strip():
            return ("", "")

        # Clean and normalize
        name = full_name.strip()
        parts = [p for p in name.split() if p]  # Remove empty parts

        if len(parts) == 0:
            return ("", "")
        elif len(parts) == 1:
            # Single word - assume it's a first name
            return (parts[0], "")

        # Route to appropriate parser based on company
        if "TAJIBOS" in self.company:
            return self._parse_lastname_first(parts)
        else:
            return self._parse_firstname_first(parts)

    def _parse_lastname_first(self, parts: List[str]) -> Tuple[str, str]:
        """
        Parse LOS TAJIBOS format: Last names first, then first names.

        Heuristics:
        - Check for known first names in the list
        - Typically 2 last names, 1-2 first names
        - If 2 parts: first=last, second=first
        - If 3 parts: first two=last, third=first
        - If 4+ parts: first two=last, rest=first
        """
        parts_lower = [p.lower() for p in parts]

        # Find the first occurrence of a known first name
        first_name_idx = None
        for i, part in enumerate(parts_lower):
            if part in self.COMMON_FIRST_NAMES:
                first_name_idx = i
                break

        if first_name_idx is not None and first_name_idx > 0:
            # Found a first name - everything before is last name
            last_name = ' '.join(parts[:first_name_idx])
            first_name = ' '.join(parts[first_name_idx:])
        elif len(parts) == 2:
            # Two parts: first=last, second=first
            last_name = parts[0]
            first_name = parts[1]
        elif len(parts) == 3:
            # Three parts: first two=last, third=first
            last_name = ' '.join(parts[:2])
            first_name = parts[2]
        else:
            # Four or more: first two=last, rest=first
            last_name = ' '.join(parts[:2])
            first_name = ' '.join(parts[2:])

        return (first_name, last_name)

    def _parse_firstname_first(self, parts: List[str]) -> Tuple[str, str]:
        """
        Parse COMVERSA/BOLIVIAN FOODS format: First names first, then last names.

        Heuristics:
        - If 2 parts: first=first, second=last
        - If 3 parts: first=first, last two=last
        - If 4+ parts: first two=first, rest=last (or first=first, rest=last if no compound)
        """
        parts_lower = [p.lower() for p in parts]

        # Check for compound last names (de, del, etc.)
        compound_idx = None
        for i, part in enumerate(parts_lower[1:], start=1):  # Skip first part
            if part in self.COMPOUND_INDICATORS:
                compound_idx = i
                break

        if compound_idx is not None:
            # Found compound indicator - everything before is first, rest is last
            first_name = ' '.join(parts[:compound_idx])
            last_name = ' '.join(parts[compound_idx:])
        elif len(parts) == 2:
            # Two parts: first=first, second=last
            first_name = parts[0]
            last_name = parts[1]
        elif len(parts) == 3:
            # Three parts: check if first part is a known first name
            if parts_lower[0] in self.COMMON_FIRST_NAMES:
                first_name = parts[0]
                last_name = ' '.join(parts[1:])
            else:
                # Assume first two are first names
                first_name = ' '.join(parts[:2])
                last_name = parts[2]
        else:
            # Four or more: check pattern
            # If first word is common first name, it's likely first=first, rest=last
            if parts_lower[0] in self.COMMON_FIRST_NAMES:
                first_name = parts[0]
                last_name = ' '.join(parts[1:])
            else:
                # Assume first two are first names, rest are last names
                first_name = ' '.join(parts[:2])
                last_name = ' '.join(parts[2:])

        return (first_name, last_name)


def clean_employee_names(input_file: Path, output_file: Path) -> None:
    """
    Process employee CSV, splitting names into first and last names.

    Args:
        input_file: Path to input CSV
        output_file: Path to output CSV
    """
    with open(input_file, 'r', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)

        # Prepare output headers
        fieldnames = ['fname', 'lname'] + [
            field for field in reader.fieldnames
            if field and field != 'Nombre' and field != '\ufeffNombre'
        ]

        rows_processed = []
        stats = {
            'total': 0,
            'by_company': {},
            'parsing_issues': []
        }

        for row in reader:
            stats['total'] += 1

            # Get full name (handle BOM if present)
            full_name = row.get('Nombre') or row.get('\ufeffNombre', '')
            company = row.get('Empresa', '')

            if not full_name.strip():
                continue

            # Parse name
            parser = NameParser(company)
            fname, lname = parser.parse(full_name)

            # Track statistics
            if company not in stats['by_company']:
                stats['by_company'][company] = {
                    'count': 0,
                    'examples': []
                }
            stats['by_company'][company]['count'] += 1
            if len(stats['by_company'][company]['examples']) < 3:
                stats['by_company'][company]['examples'].append(
                    f"{full_name} → {fname} | {lname}"
                )

            # Warn about potential issues
            if not fname or not lname:
                stats['parsing_issues'].append(f"Issue with: {full_name} (Company: {company})")

            # Create new row
            new_row = {
                'fname': fname,
                'lname': lname
            }

            # Copy other fields
            for field in fieldnames[2:]:
                new_row[field] = row.get(field, '')

            rows_processed.append(new_row)

        # Write output
        with open(output_file, 'w', encoding='utf-8', newline='') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_processed)

        # Print statistics
        print(f"\n✅ Processed {stats['total']} employees")
        print(f"📄 Output saved to: {output_file}")
        print("\n📊 Statistics by Company:")
        for company, data in stats['by_company'].items():
            print(f"\n  {company}: {data['count']} employees")
            print("  Examples:")
            for example in data['examples']:
                print(f"    {example}")

        if stats['parsing_issues']:
            print(f"\n⚠️  Found {len(stats['parsing_issues'])} potential parsing issues:")
            for issue in stats['parsing_issues'][:10]:  # Show first 10
                print(f"    {issue}")


def main():
    """Main entry point."""
    # Determine paths
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / 'data' / 'company_info' / 'Complete Reports' / 'perfiles_gc_index_completo_44_empleados.csv'
    output_file = base_dir / 'data' / 'company_info' / 'Complete Reports' / 'perfiles_gc_index_completo_44_empleados_cleaned.csv'

    if not input_file.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)

    print(f"🔄 Processing employee names...")
    print(f"📂 Input: {input_file.name}")
    print(f"📂 Output: {output_file.name}")

    clean_employee_names(input_file, output_file)

    print("\n✅ Done! Review the output file and verify the name splits.")
    print("\n💡 Next steps:")
    print("   1. Review the cleaned CSV file")
    print("   2. Verify name splits are correct")
    print("   3. Integrate into the intelligence capture system")


if __name__ == '__main__':
    main()
