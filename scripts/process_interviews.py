#!/usr/bin/env python3
"""Process manager interview CSVs and extract structured insights"""

import csv
import json
from collections import defaultdict
from pathlib import Path

def process_csv(filepath):
    """Extract structured data from interview CSV"""
    interviews = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Extract QA pairs
            qa_pairs = {}
            for i in range(1, 11):
                q_key = f'Pregunta {i}'
                a_key = f'Respuesta {i}'
                if q_key in row and a_key in row and row[a_key]:
                    qa_pairs[row[q_key]] = row[a_key]

            if qa_pairs:  # Only include if has responses
                interview = {
                    'meta': {
                        'company': row.get('Compañia', ''),
                        'respondent': row.get('Nombre', ''),
                        'role': row.get('Cargo', ''),
                        'date': row.get('Fecha', '')
                    },
                    'qa_pairs': qa_pairs
                }
                interviews.append(interview)

    return interviews

def extract_insights(interviews):
    """Extract pain points, tools, processes from interviews"""

    tools_mentioned = defaultdict(int)
    pain_keywords = ['problema', 'dificultad', 'desafío', 'lento', 'manual', 'retraso', 'demora',
                     'falta', 'duplicado', 'repetitivo', 'ineficiente', 'complicado', 'confuso']
    systems_keywords = ['SAP', 'Excel', 'Opera', 'Simphony', 'Micros', 'Satcom', 'WhatsApp',
                       'MaintainX', 'CMNET', 'Power BI', 'Outlook', 'Teams']

    insights = {
        'roles': [],
        'systems': defaultdict(list),
        'pain_points': [],
        'processes': []
    }

    for interview in interviews:
        role_info = {
            'company': interview['meta']['company'],
            'role': interview['meta']['role'],
            'name': interview['meta']['respondent']
        }
        insights['roles'].append(role_info)

        # Extract from all responses
        for question, answer in interview['qa_pairs'].items():
            answer_lower = answer.lower()

            # Find systems/tools
            for system in systems_keywords:
                if system.lower() in answer_lower:
                    tools_mentioned[system] += 1
                    insights['systems'][system].append(role_info['role'])

            # Find pain points
            for pain_word in pain_keywords:
                if pain_word in answer_lower:
                    insights['pain_points'].append({
                        'role': role_info['role'],
                        'company': role_info['company'],
                        'context': answer[:200]  # First 200 chars
                    })
                    break  # Only capture once per answer

    # Sort tools by frequency
    insights['top_tools'] = sorted(tools_mentioned.items(), key=lambda x: x[1], reverse=True)[:15]

    return insights

def main():
    base_path = Path('/Users/tatooine/Documents/Development/Comversa/system0')

    csv_files = [
        'SOCIEDAD HOTELERA _LOS TAJIBOS_ S.A. - Sheet1.csv',
        'COMPAÑIA DE INVERSIONES COMVERSA S.A. - Sheet1.csv',
        'BOLIVIAN FOODS S.A. - Sheet1.csv'
    ]

    all_interviews = []
    company_data = {}

    for csv_file in csv_files:
        filepath = base_path / csv_file
        if filepath.exists():
            print(f"Processing {csv_file}...")
            interviews = process_csv(filepath)
            all_interviews.extend(interviews)

            company_name = csv_file.split(' - ')[0]
            company_data[company_name] = {
                'interview_count': len(interviews),
                'roles': [i['meta']['role'] for i in interviews]
            }

    # Extract insights
    insights = extract_insights(all_interviews)

    # Generate summary
    summary = {
        'total_interviews': len(all_interviews),
        'companies': company_data,
        'top_systems': insights['top_tools'],
        'pain_point_count': len(insights['pain_points']),
        'unique_roles': len(set([r['role'] for r in insights['roles']]))
    }

    # Save outputs
    output_path = base_path / 'analysis_output'
    output_path.mkdir(exist_ok=True)

    with open(output_path / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(output_path / 'insights.json', 'w', encoding='utf-8') as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)

    with open(output_path / 'all_interviews.json', 'w', encoding='utf-8') as f:
        json.dump(all_interviews, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Processed {len(all_interviews)} interviews")
    print(f"📊 Top 10 systems: {insights['top_tools'][:10]}")
    print(f"⚠️  Pain points identified: {len(insights['pain_points'])}")
    print(f"\nOutput saved to: {output_path}")

if __name__ == '__main__':
    main()
