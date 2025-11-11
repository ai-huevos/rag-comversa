#!/usr/bin/env python3
"""
Generate Priority Matrices from Extracted Intelligence

Generates 3 strategic priority matrices:
1. Pain Points Priority Matrix (Impact vs Frequency)
2. Automation Opportunities Matrix (ROI vs Implementation Difficulty)
3. Strategic Investment Matrix (Cost vs Benefit)

Usage:
    python scripts/generate_priority_matrices.py

Output:
    - reports/priority_matrices/pain_points_matrix.md
    - reports/priority_matrices/automation_matrix.md
    - reports/priority_matrices/investment_matrix.md
    - reports/priority_matrices/executive_summary.md
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from intelligence_capture.config import DB_PATH

# Ensure output directory exists
OUTPUT_DIR = Path("reports/priority_matrices")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_db_connection():
    """Connect to SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def frequency_to_score(frequency: str) -> int:
    """Convert frequency text to numeric score (1-5)"""
    frequency_lower = (frequency or "").lower()
    if "diari" in frequency_lower or "every day" in frequency_lower or "diario" in frequency_lower:
        return 5
    elif "semanal" in frequency_lower or "weekly" in frequency_lower or "semana" in frequency_lower:
        return 4
    elif "mensual" in frequency_lower or "monthly" in frequency_lower or "mes" in frequency_lower:
        return 3
    elif "trimestral" in frequency_lower or "quarterly" in frequency_lower:
        return 2
    elif "ocasional" in frequency_lower or "occasional" in frequency_lower or "rara" in frequency_lower:
        return 1
    return 3  # Default medium


def severity_to_score(severity: str) -> int:
    """Convert severity text to numeric score (1-5)"""
    severity_lower = (severity or "").lower()
    if "critical" in severity_lower or "crítico" in severity_lower:
        return 5
    elif "high" in severity_lower or "alto" in severity_lower:
        return 4
    elif "medium" in severity_lower or "medio" in severity_lower:
        return 3
    elif "low" in severity_lower or "bajo" in severity_lower:
        return 2
    return 3  # Default medium


def calculate_impact_score(row: sqlite3.Row) -> int:
    """Calculate impact score from multiple factors (1-10)"""
    score = 0

    # Base severity (0-5)
    score += severity_to_score(row['severity'])

    # Hair on fire indicator (+3)
    if row['hair_on_fire']:
        score += 3

    # Annual cost impact (+2 if significant)
    if row['estimated_annual_cost_usd'] and row['estimated_annual_cost_usd'] > 10000:
        score += 2

    # Cap at 10
    return min(score, 10)


def generate_pain_points_matrix() -> Tuple[str, Dict]:
    """Generate Pain Points Priority Matrix (Impact vs Frequency)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            company,
            business_unit,
            department,
            description,
            frequency,
            severity,
            hair_on_fire,
            time_wasted_per_occurrence_minutes,
            estimated_annual_cost_usd,
            affected_roles
        FROM pain_points
        WHERE description IS NOT NULL
        ORDER BY severity DESC, frequency DESC
    """)

    pain_points = cursor.fetchall()

    # Categorize into quadrants
    quadrants = {
        'critical': [],      # High Impact + High Frequency (Top Priority)
        'important': [],     # High Impact + Low Frequency (Strategic)
        'irritant': [],      # Low Impact + High Frequency (Quick Wins)
        'monitor': []        # Low Impact + Low Frequency (Monitor)
    }

    stats = {
        'total': len(pain_points),
        'by_company': defaultdict(int),
        'by_severity': defaultdict(int),
        'total_annual_cost': 0
    }

    for row in pain_points:
        impact = calculate_impact_score(row)
        frequency = frequency_to_score(row['frequency'])

        # Update stats
        stats['by_company'][row['company']] += 1
        stats['by_severity'][row['severity']] += 1
        if row['estimated_annual_cost_usd']:
            stats['total_annual_cost'] += row['estimated_annual_cost_usd']

        item = {
            'id': row['id'],
            'company': row['company'],
            'business_unit': row['business_unit'],
            'department': row['department'],
            'description': row['description'][:100] + '...' if len(row['description']) > 100 else row['description'],
            'impact_score': impact,
            'frequency_score': frequency,
            'severity': row['severity'],
            'hair_on_fire': bool(row['hair_on_fire']),
            'annual_cost_usd': row['estimated_annual_cost_usd'] or 0,
            'affected_roles': row['affected_roles']
        }

        # Categorize into quadrant
        if impact >= 7 and frequency >= 4:
            quadrants['critical'].append(item)
        elif impact >= 7 and frequency < 4:
            quadrants['important'].append(item)
        elif impact < 7 and frequency >= 4:
            quadrants['irritant'].append(item)
        else:
            quadrants['monitor'].append(item)

    conn.close()

    # Generate markdown report
    report = f"""# 🔥 Pain Points Priority Matrix

**Impact vs Frequency Analysis**

Generated from {stats['total']} pain points across 44 manager interviews.

---

## 📊 Executive Summary

- **Total Pain Points Analyzed:** {stats['total']}
- **Estimated Total Annual Cost:** ${stats['total_annual_cost']:,.2f} USD
- **Critical Issues (Fix Now):** {len(quadrants['critical'])}
- **Strategic Issues (Plan):** {len(quadrants['important'])}
- **Quick Wins (Low Effort):** {len(quadrants['irritant'])}
- **Monitor Items:** {len(quadrants['monitor'])}

### By Company
"""

    for company, count in sorted(stats['by_company'].items(), key=lambda x: x[1], reverse=True):
        report += f"- **{company}:** {count} pain points\n"

    report += "\n---\n\n## 🎯 Priority Matrix\n\n"
    report += "```\n"
    report += "        High Impact │\n"
    report += "                   │\n"
    report += f"   IMPORTANT ({len(quadrants['important']):2d})  │  CRITICAL ({len(quadrants['critical']):2d})\n"
    report += "    Strategic      │  Fix Now!\n"
    report += "                   │\n"
    report += "─────────────────────────────────────\n"
    report += "                   │\n"
    report += f"    MONITOR ({len(quadrants['monitor']):2d})    │  IRRITANT ({len(quadrants['irritant']):2d})\n"
    report += "    Low Priority   │  Quick Wins\n"
    report += "                   │\n"
    report += "        Low Impact │\n"
    report += "                   \n"
    report += "           Low ←─── Frequency ───→ High\n"
    report += "```\n\n"

    # Critical Issues (Top Priority)
    report += "## 🚨 CRITICAL: Fix Immediately\n\n"
    report += "*High Impact + High Frequency - These are burning issues affecting operations daily*\n\n"

    if quadrants['critical']:
        for item in sorted(quadrants['critical'], key=lambda x: (x['impact_score'], x['frequency_score']), reverse=True)[:10]:
            fire = "🔥" if item['hair_on_fire'] else ""
            cost = f" (${item['annual_cost_usd']:,.0f}/year)" if item['annual_cost_usd'] > 0 else ""
            report += f"- **{item['company']} - {item['business_unit']}** {fire}\n"
            report += f"  - {item['description']}\n"
            report += f"  - Impact: {item['impact_score']}/10 | Frequency: {item['frequency_score']}/5{cost}\n\n"
    else:
        report += "*No critical issues identified*\n\n"

    # Important Issues (Strategic)
    report += "## ⚡ IMPORTANT: Strategic Planning Required\n\n"
    report += "*High Impact + Low Frequency - Significant but not urgent*\n\n"

    if quadrants['important']:
        for item in sorted(quadrants['important'], key=lambda x: x['impact_score'], reverse=True)[:10]:
            cost = f" (${item['annual_cost_usd']:,.0f}/year)" if item['annual_cost_usd'] > 0 else ""
            report += f"- **{item['company']} - {item['business_unit']}**\n"
            report += f"  - {item['description']}\n"
            report += f"  - Impact: {item['impact_score']}/10{cost}\n\n"
    else:
        report += "*No strategic issues identified*\n\n"

    # Quick Wins (Irritants)
    report += "## 💡 IRRITANT: Quick Wins Possible\n\n"
    report += "*Low Impact + High Frequency - Annoying but fixable*\n\n"

    if quadrants['irritant']:
        for item in sorted(quadrants['irritant'], key=lambda x: x['frequency_score'], reverse=True)[:10]:
            report += f"- **{item['company']} - {item['business_unit']}**\n"
            report += f"  - {item['description']}\n"
            report += f"  - Frequency: {item['frequency_score']}/5\n\n"
    else:
        report += "*No quick win opportunities identified*\n\n"

    return report, {
        'quadrants': {k: len(v) for k, v in quadrants.items()},
        'stats': dict(stats)
    }


def generate_automation_matrix() -> Tuple[str, Dict]:
    """Generate Automation Opportunities Matrix (ROI vs Implementation Difficulty)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            company,
            business_unit,
            department,
            name,
            process,
            complexity,
            impact,
            effort_score,
            impact_score,
            priority_quadrant,
            estimated_roi_months,
            estimated_annual_savings_usd,
            ceo_priority,
            overlooked_opportunity
        FROM automation_candidates
        WHERE name IS NOT NULL
        ORDER BY estimated_annual_savings_usd DESC NULLS LAST
    """)

    automations = cursor.fetchall()

    # Categorize into quadrants
    quadrants = {
        'quick_wins': [],      # High ROI + Easy Implementation
        'strategic': [],       # High ROI + Hard Implementation
        'fill_ins': [],        # Low ROI + Easy Implementation
        'time_sinks': []       # Low ROI + Hard Implementation
    }

    stats = {
        'total': len(automations),
        'by_company': defaultdict(int),
        'total_potential_savings': 0,
        'ceo_priorities': 0
    }

    for row in automations:
        # Use effort_score (inverse: higher = harder) and impact_score
        effort = row['effort_score'] or 5  # Default medium
        roi_value = row['impact_score'] or 5  # Default medium

        # Update stats
        stats['by_company'][row['company']] += 1
        if row['estimated_annual_savings_usd']:
            stats['total_potential_savings'] += row['estimated_annual_savings_usd']
        if row['ceo_priority']:
            stats['ceo_priorities'] += 1

        item = {
            'id': row['id'],
            'company': row['company'],
            'business_unit': row['business_unit'],
            'department': row['department'],
            'name': row['name'],
            'process': row['process'],
            'effort_score': effort,
            'roi_score': roi_value,
            'complexity': row['complexity'],
            'annual_savings': row['estimated_annual_savings_usd'] or 0,
            'roi_months': row['estimated_roi_months'],
            'ceo_priority': bool(row['ceo_priority']),
            'overlooked': bool(row['overlooked_opportunity'])
        }

        # Categorize (lower effort = easier)
        if roi_value >= 7 and effort <= 5:
            quadrants['quick_wins'].append(item)
        elif roi_value >= 7 and effort > 5:
            quadrants['strategic'].append(item)
        elif roi_value < 7 and effort <= 5:
            quadrants['fill_ins'].append(item)
        else:
            quadrants['time_sinks'].append(item)

    conn.close()

    # Generate markdown report
    report = f"""# 🤖 Automation Opportunities Matrix

**ROI vs Implementation Difficulty Analysis**

Generated from {stats['total']} automation candidates across 44 manager interviews.

---

## 📊 Executive Summary

- **Total Opportunities Analyzed:** {stats['total']}
- **Total Potential Annual Savings:** ${stats['total_potential_savings']:,.2f} USD
- **Quick Wins (Do First):** {len(quadrants['quick_wins'])}
- **Strategic Projects (Plan):** {len(quadrants['strategic'])}
- **Fill-In Tasks:** {len(quadrants['fill_ins'])}
- **CEO Priorities:** {stats['ceo_priorities']}

### By Company
"""

    for company, count in sorted(stats['by_company'].items(), key=lambda x: x[1], reverse=True):
        report += f"- **{company}:** {count} opportunities\n"

    report += "\n---\n\n## 🎯 Priority Matrix\n\n"
    report += "```\n"
    report += "        High ROI   │\n"
    report += "                   │\n"
    report += f"   STRATEGIC ({len(quadrants['strategic']):2d})   │  QUICK WINS ({len(quadrants['quick_wins']):2d})\n"
    report += "   Major Projects │  Do These First!\n"
    report += "                   │\n"
    report += "─────────────────────────────────────\n"
    report += "                   │\n"
    report += f"  TIME SINKS ({len(quadrants['time_sinks']):2d})   │  FILL-INS ({len(quadrants['fill_ins']):2d})\n"
    report += "   Avoid These    │  If Time Permits\n"
    report += "                   │\n"
    report += "         Low ROI   │\n"
    report += "                   \n"
    report += "        Hard ←─── Difficulty ───→ Easy\n"
    report += "```\n\n"

    # Quick Wins
    report += "## ✅ QUICK WINS: Do These First!\n\n"
    report += "*High ROI + Easy Implementation - Immediate value*\n\n"

    if quadrants['quick_wins']:
        for item in sorted(quadrants['quick_wins'], key=lambda x: x['annual_savings'], reverse=True)[:10]:
            ceo = "⭐ CEO Priority" if item['ceo_priority'] else ""
            hidden = "💎 Overlooked!" if item['overlooked'] else ""
            savings = f"${item['annual_savings']:,.0f}/year" if item['annual_savings'] > 0 else "Savings TBD"
            report += f"- **{item['company']} - {item['business_unit']}** {ceo} {hidden}\n"
            report += f"  - **{item['name']}**\n"
            report += f"  - Process: {item['process']}\n"
            report += f"  - ROI: {item['roi_score']}/10 | Effort: {item['effort_score']}/10 | Savings: {savings}\n\n"
    else:
        report += "*No quick wins identified*\n\n"

    # Strategic Projects
    report += "## 🎯 STRATEGIC: Major Projects Worth Planning\n\n"
    report += "*High ROI + Complex Implementation - Significant value, needs planning*\n\n"

    if quadrants['strategic']:
        for item in sorted(quadrants['strategic'], key=lambda x: x['annual_savings'], reverse=True)[:10]:
            ceo = "⭐ CEO Priority" if item['ceo_priority'] else ""
            savings = f"${item['annual_savings']:,.0f}/year" if item['annual_savings'] > 0 else "Savings TBD"
            report += f"- **{item['company']} - {item['business_unit']}** {ceo}\n"
            report += f"  - **{item['name']}**\n"
            report += f"  - Process: {item['process']}\n"
            report += f"  - ROI: {item['roi_score']}/10 | Complexity: {item['complexity']} | Savings: {savings}\n\n"
    else:
        report += "*No strategic projects identified*\n\n"

    # Fill-Ins
    report += "## 🔧 FILL-INS: If Time Permits\n\n"
    report += "*Low ROI + Easy Implementation - Nice to have*\n\n"

    if quadrants['fill_ins']:
        for item in sorted(quadrants['fill_ins'], key=lambda x: x['effort_score'])[:5]:
            report += f"- **{item['company']}**: {item['name']}\n"
    else:
        report += "*No fill-in opportunities identified*\n\n"

    return report, {
        'quadrants': {k: len(v) for k, v in quadrants.items()},
        'stats': dict(stats)
    }


def generate_investment_matrix() -> Tuple[str, Dict]:
    """Generate Strategic Investment Matrix (Cost vs Benefit)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Combine pain points and automations for investment analysis
    cursor.execute("""
        SELECT
            'pain_point' as type,
            id,
            company,
            business_unit,
            department,
            description as name,
            estimated_annual_cost_usd as cost,
            severity,
            hair_on_fire as priority_flag
        FROM pain_points
        WHERE estimated_annual_cost_usd > 0

        UNION ALL

        SELECT
            'automation' as type,
            id,
            company,
            business_unit,
            department,
            name,
            estimated_annual_savings_usd as cost,
            impact as severity,
            ceo_priority as priority_flag
        FROM automation_candidates
        WHERE estimated_annual_savings_usd > 0

        ORDER BY cost DESC
    """)

    investments = cursor.fetchall()

    # Categorize into quadrants
    quadrants = {
        'strategic': [],       # High Cost + High Benefit (Major investments)
        'quick_wins': [],      # Low Cost + High Benefit (Do immediately)
        'reconsider': [],      # High Cost + Low Benefit (Question these)
        'incremental': []      # Low Cost + Low Benefit (Small improvements)
    }

    stats = {
        'total': len(investments),
        'total_cost': 0,
        'pain_point_cost': 0,
        'automation_savings': 0,
        'by_company': defaultdict(lambda: {'cost': 0, 'count': 0})
    }

    for row in investments:
        cost = row['cost'] or 0
        benefit = severity_to_score(row['severity']) * 2  # Scale to 10

        # Update stats
        stats['total_cost'] += cost
        if row['type'] == 'pain_point':
            stats['pain_point_cost'] += cost
        else:
            stats['automation_savings'] += cost

        stats['by_company'][row['company']]['cost'] += cost
        stats['by_company'][row['company']]['count'] += 1

        item = {
            'type': row['type'],
            'id': row['id'],
            'company': row['company'],
            'business_unit': row['business_unit'],
            'department': row['department'],
            'name': row['name'],
            'cost': cost,
            'benefit_score': benefit,
            'severity': row['severity'],
            'priority': bool(row['priority_flag'])
        }

        # Categorize (using median cost as threshold)
        median_cost = 50000  # $50K threshold
        if cost >= median_cost and benefit >= 7:
            quadrants['strategic'].append(item)
        elif cost < median_cost and benefit >= 7:
            quadrants['quick_wins'].append(item)
        elif cost >= median_cost and benefit < 7:
            quadrants['reconsider'].append(item)
        else:
            quadrants['incremental'].append(item)

    conn.close()

    # Generate markdown report
    report = f"""# 💰 Strategic Investment Matrix

**Cost vs Benefit Analysis**

Generated from {stats['total']} investment opportunities (pain points + automations).

---

## 📊 Executive Summary

- **Total Opportunities Analyzed:** {stats['total']}
- **Total Pain Point Costs:** ${stats['pain_point_cost']:,.2f} USD/year
- **Total Automation Savings:** ${stats['automation_savings']:,.2f} USD/year
- **Net Opportunity:** ${stats['automation_savings'] - stats['pain_point_cost']:,.2f} USD/year
- **Strategic Investments:** {len(quadrants['strategic'])}
- **Quick Wins:** {len(quadrants['quick_wins'])}

### By Company (Investment Opportunity)
"""

    for company, data in sorted(stats['by_company'].items(), key=lambda x: x[1]['cost'], reverse=True):
        report += f"- **{company}:** ${data['cost']:,.0f} ({data['count']} items)\n"

    report += "\n---\n\n## 🎯 Investment Matrix\n\n"
    report += "```\n"
    report += "     High Benefit │\n"
    report += "                  │\n"
    report += f"  QUICK WINS ({len(quadrants['quick_wins']):2d}) │  STRATEGIC ({len(quadrants['strategic']):2d})\n"
    report += "    Do Now!      │  Major Projects\n"
    report += "                  │\n"
    report += "────────────────────────────────────\n"
    report += "                  │\n"
    report += f" INCREMENTAL ({len(quadrants['incremental']):2d}) │  RECONSIDER ({len(quadrants['reconsider']):2d})\n"
    report += "  Small Wins     │  Question ROI\n"
    report += "                  │\n"
    report += "      Low Benefit │\n"
    report += "                  \n"
    report += "      Low ←─── Cost ───→ High\n"
    report += "```\n\n"

    # Strategic Investments
    report += "## 🎯 STRATEGIC: Major Investments\n\n"
    report += "*High Cost + High Benefit - Significant projects worth the investment*\n\n"

    if quadrants['strategic']:
        for item in sorted(quadrants['strategic'], key=lambda x: x['cost'], reverse=True)[:10]:
            priority = "⭐ Priority" if item['priority'] else ""
            type_label = "💰 Savings Opportunity" if item['type'] == 'automation' else "🔥 Cost Reduction"
            report += f"- **{item['company']} - {item['business_unit']}** {priority}\n"
            report += f"  - {item['name'][:80]}{'...' if len(item['name']) > 80 else ''}\n"
            report += f"  - ${item['cost']:,.0f}/year | Benefit: {item['benefit_score']}/10 | {type_label}\n\n"
    else:
        report += "*No strategic investments identified*\n\n"

    # Quick Wins
    report += "## ✅ QUICK WINS: Do These Immediately\n\n"
    report += "*Low Cost + High Benefit - Best ROI opportunities*\n\n"

    if quadrants['quick_wins']:
        for item in sorted(quadrants['quick_wins'], key=lambda x: x['benefit_score'], reverse=True)[:10]:
            priority = "⭐ Priority" if item['priority'] else ""
            type_label = "💰 Savings" if item['type'] == 'automation' else "🔥 Cost Cut"
            report += f"- **{item['company']}** {priority}\n"
            report += f"  - {item['name'][:80]}{'...' if len(item['name']) > 80 else ''}\n"
            report += f"  - ${item['cost']:,.0f}/year | Benefit: {item['benefit_score']}/10 | {type_label}\n\n"
    else:
        report += "*No quick wins identified*\n\n"

    # Reconsider
    report += "## ⚠️ RECONSIDER: Question These Investments\n\n"
    report += "*High Cost + Low Benefit - May not be worth it*\n\n"

    if quadrants['reconsider']:
        for item in sorted(quadrants['reconsider'], key=lambda x: x['cost'], reverse=True)[:5]:
            report += f"- **{item['company']}**: ${item['cost']:,.0f}/year - {item['name'][:60]}\n"
    else:
        report += "*All high-cost investments have good ROI*\n\n"

    return report, {
        'quadrants': {k: len(v) for k, v in quadrants.items()},
        'stats': dict(stats)
    }


def generate_executive_summary(pain_stats: Dict, auto_stats: Dict, invest_stats: Dict) -> str:
    """Generate executive summary combining all matrices"""
    report = f"""# 📊 Executive Priority Matrices - Strategic Overview

**Intelligence Analysis from 44 Manager Interviews**

Generated: {Path(__file__).name}

---

## 🎯 Three Strategic Lenses

This analysis provides three complementary views of organizational priorities:

1. **Pain Points Matrix** - What hurts most and how often?
2. **Automation Matrix** - What should we automate first?
3. **Investment Matrix** - Where should we invest resources?

---

## 📈 Key Findings

### Pain Points Analysis
- **Total Issues Identified:** {pain_stats['stats']['total']}
- **Critical (Fix Now):** {pain_stats['quadrants']['critical']}
- **Strategic Planning Needed:** {pain_stats['quadrants']['important']}
- **Quick Wins Available:** {pain_stats['quadrants']['irritant']}
- **Total Annual Cost:** ${pain_stats['stats']['total_annual_cost']:,.2f}

### Automation Opportunities
- **Total Opportunities:** {auto_stats['stats']['total']}
- **Quick Win Automations:** {auto_stats['quadrants']['quick_wins']}
- **Strategic Projects:** {auto_stats['quadrants']['strategic']}
- **Potential Annual Savings:** ${auto_stats['stats']['total_potential_savings']:,.2f}
- **CEO Priorities Identified:** {auto_stats['stats']['ceo_priorities']}

### Investment Analysis
- **Total Investment Opportunities:** {invest_stats['stats']['total']}
- **High-Priority Strategic Investments:** {invest_stats['quadrants']['strategic']}
- **Quick Win Investments:** {invest_stats['quadrants']['quick_wins']}
- **Net Annual Opportunity:** ${invest_stats['stats']['automation_savings'] - invest_stats['stats']['pain_point_cost']:,.2f}

---

## 🚀 Recommended Action Plan

### Immediate Actions (Next 30 Days)
1. **Address Critical Pain Points** - {pain_stats['quadrants']['critical']} issues requiring immediate attention
2. **Launch Quick Win Automations** - {auto_stats['quadrants']['quick_wins']} opportunities with immediate ROI
3. **Approve Quick Win Investments** - {invest_stats['quadrants']['quick_wins']} low-cost, high-benefit projects

### Short-Term Planning (90 Days)
1. **Strategic Pain Point Mitigation** - Plan for {pain_stats['quadrants']['important']} high-impact issues
2. **Major Automation Roadmap** - Design {auto_stats['quadrants']['strategic']} strategic automation projects
3. **Resource Allocation** - Budget for {invest_stats['quadrants']['strategic']} strategic investments

### Long-Term Strategy (12 Months)
1. **Process Optimization** - Address {pain_stats['quadrants']['irritant']} frequent irritants
2. **Technology Transformation** - Complete strategic automation initiatives
3. **Continuous Improvement** - Monitor and iterate based on results

---

## 📋 Detailed Reports

For detailed analysis, see:
- [Pain Points Priority Matrix](pain_points_matrix.md)
- [Automation Opportunities Matrix](automation_matrix.md)
- [Strategic Investment Matrix](investment_matrix.md)

---

**Data Source:** 44 manager interviews across Los Tajibos, Comversa, Bolivian Foods
**Analysis Method:** Multi-dimensional priority scoring (Impact, Frequency, ROI, Cost)
**Confidence Level:** High (based on comprehensive interview data)
"""

    return report


def main():
    """Generate all priority matrices"""
    print("=" * 60)
    print("GENERATING PRIORITY MATRICES")
    print("=" * 60)

    print("\n1️⃣  Generating Pain Points Matrix...")
    pain_report, pain_stats = generate_pain_points_matrix()
    pain_file = OUTPUT_DIR / "pain_points_matrix.md"
    pain_file.write_text(pain_report, encoding='utf-8')
    print(f"   ✅ Saved to {pain_file}")

    print("\n2️⃣  Generating Automation Opportunities Matrix...")
    auto_report, auto_stats = generate_automation_matrix()
    auto_file = OUTPUT_DIR / "automation_matrix.md"
    auto_file.write_text(auto_report, encoding='utf-8')
    print(f"   ✅ Saved to {auto_file}")

    print("\n3️⃣  Generating Strategic Investment Matrix...")
    invest_report, invest_stats = generate_investment_matrix()
    invest_file = OUTPUT_DIR / "investment_matrix.md"
    invest_file.write_text(invest_report, encoding='utf-8')
    print(f"   ✅ Saved to {invest_file}")

    print("\n4️⃣  Generating Executive Summary...")
    exec_report = generate_executive_summary(pain_stats, auto_stats, invest_stats)
    exec_file = OUTPUT_DIR / "executive_summary.md"
    exec_file.write_text(exec_report, encoding='utf-8')
    print(f"   ✅ Saved to {exec_file}")

    # Generate JSON summary for programmatic access
    summary_json = {
        'pain_points': pain_stats,
        'automation': auto_stats,
        'investment': invest_stats,
        'generated_at': str(Path(__file__).stat().st_mtime)
    }

    json_file = OUTPUT_DIR / "matrices_summary.json"
    json_file.write_text(json.dumps(summary_json, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"   ✅ Saved JSON summary to {json_file}")

    print("\n" + "=" * 60)
    print("✨ ALL PRIORITY MATRICES GENERATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\n📂 Output Directory: {OUTPUT_DIR.absolute()}")
    print("\nGenerated Files:")
    print(f"  1. {exec_file.name} - Start here for overview")
    print(f"  2. {pain_file.name}")
    print(f"  3. {auto_file.name}")
    print(f"  4. {invest_file.name}")
    print(f"  5. {json_file.name}")

    print("\n🎯 Quick Stats:")
    print(f"  • Critical Pain Points: {pain_stats['quadrants']['critical']}")
    print(f"  • Quick Win Automations: {auto_stats['quadrants']['quick_wins']}")
    print(f"  • Strategic Investments: {invest_stats['quadrants']['strategic']}")
    print(f"  • Total Potential Savings: ${auto_stats['stats']['total_potential_savings']:,.2f}/year")


if __name__ == "__main__":
    main()
