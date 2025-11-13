"""
AI-powered extraction of structured intelligence from interview responses
Uses GPT-4 to extract entities based on PHASE1_ONTOLOGY_SCHEMA.json
Orchestrates v1.0 and v2.0 extractors for all 17 entity types
"""
import json
from typing import Dict, List, Any
from openai import OpenAI
from .config import OPENAI_API_KEY, MODEL, TEMPERATURE, MAX_RETRIES
from .rate_limiter import get_rate_limiter

# Import all v2.0 extractors
from .extractors import (
    CommunicationChannelExtractor,
    SystemExtractor,
    DecisionPointExtractor,
    DataFlowExtractor,
    TemporalPatternExtractor,
    FailureModeExtractor,
    EnhancedPainPointExtractor,
    AutomationCandidateExtractor,
    TeamStructureExtractor,
    KnowledgeGapExtractor,
    SuccessPatternExtractor,
    BudgetConstraintExtractor,
    ExternalDependencyExtractor
)


class IntelligenceExtractor:
    """Extracts structured data from interview responses using GPT-4"""

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.rate_limiter = get_rate_limiter(max_calls_per_minute=50, key="legacy:gpt-4o-mini")

        # Initialize all v2.0 extractors
        print("🔧 Initializing extractors...")
        self.v2_extractors = {
            "communication_channels": CommunicationChannelExtractor(OPENAI_API_KEY),
            "systems_v2": SystemExtractor(OPENAI_API_KEY),
            "decision_points": DecisionPointExtractor(OPENAI_API_KEY),
            "data_flows": DataFlowExtractor(OPENAI_API_KEY),
            "temporal_patterns": TemporalPatternExtractor(OPENAI_API_KEY),
            "failure_modes": FailureModeExtractor(OPENAI_API_KEY),
            "pain_points_v2": EnhancedPainPointExtractor(OPENAI_API_KEY),
            "automation_candidates_v2": AutomationCandidateExtractor(OPENAI_API_KEY),
            "team_structures": TeamStructureExtractor(OPENAI_API_KEY),
            "knowledge_gaps": KnowledgeGapExtractor(OPENAI_API_KEY),
            "success_patterns": SuccessPatternExtractor(OPENAI_API_KEY),
            "budget_constraints": BudgetConstraintExtractor(OPENAI_API_KEY),
            "external_dependencies": ExternalDependencyExtractor(OPENAI_API_KEY)
        }
        print(f"✓ Initialized {len(self.v2_extractors)} v2.0 extractors")
        
    def extract_all(self, meta: Dict, qa_pairs: Dict) -> Dict[str, List[Dict]]:
        """
        Extract all 17 entity types from an interview

        Returns:
            {
                # v1.0 entities (kept for backward compatibility)
                "pain_points": [...],
                "processes": [...],
                "systems": [...],
                "kpis": [...],
                "automation_candidates": [...],
                "inefficiencies": [...],

                # v2.0 entities (new)
                "communication_channels": [...],
                "decision_points": [...],
                "data_flows": [...],
                "temporal_patterns": [...],
                "failure_modes": [...],
                "team_structures": [...],
                "knowledge_gaps": [...],
                "success_patterns": [...],
                "budget_constraints": [...],
                "external_dependencies": [...]
            }
        """

        # Build context from interview
        interview_text = self._format_interview(meta, qa_pairs)
        interview_data = {"meta": meta, "qa_pairs": qa_pairs}

        # Extract each entity type
        results = {}

        print(f"\n🔍 Extracting from: {meta.get('respondent')} ({meta.get('role')})")

        # v1.0 extractions (legacy, for backward compatibility)
        print("  📦 Running legacy-only extractors...")
        results["processes"] = self._extract_processes(interview_text, meta)
        results["kpis"] = self._extract_kpis(interview_text, meta)
        results["inefficiencies"] = self._extract_inefficiencies(interview_text, meta)

        # v2.0 extractions (new entity types)
        print("  📦 Running v2.0 extractors...")
        for entity_type, extractor in self.v2_extractors.items():
            try:
                entities = extractor.extract_from_interview(interview_data)
                results[entity_type] = entities
                print(f"    ✓ {entity_type}: {len(entities)}")
            except Exception as e:
                print(f"    ⚠️  {entity_type} failed: {str(e)}")
                results[entity_type] = []
                # Continue processing remaining entity types

        # Project v2 entities into legacy schemas for backward compatibility
        self._project_v2_entities(results)

        return results
    
    def _format_interview(self, meta: Dict, qa_pairs: Dict) -> str:
        """Format interview for GPT-4 context"""
        lines = [
            f"ENTREVISTA",
            f"Empresa: {meta.get('company', 'Unknown')}",
            f"Entrevistado: {meta.get('respondent')}",
            f"Rol: {meta.get('role')}",
            f"Fecha: {meta.get('date')}",
            "",
            "RESPUESTAS:"
        ]
        
        for question, answer in qa_pairs.items():
            lines.append(f"\nP: {question}")
            lines.append(f"R: {answer}")
        
        return "\n".join(lines)
    
    def _call_gpt4(self, system_prompt: str, user_prompt: str) -> Dict:
        """Call GPT-4 with retry logic and rate limiting"""
        import time
        from openai import RateLimitError
        
        for attempt in range(MAX_RETRIES):
            try:
                # WAIT for rate limiter BEFORE making call
                self.rate_limiter.wait_if_needed()
                
                response = self.client.chat.completions.create(
                    model=MODEL,
                    temperature=TEMPERATURE,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                result = json.loads(response.choices[0].message.content)
                return result
                
            except RateLimitError as e:
                # Should rarely happen now with rate limiter
                wait_time = min(2 ** attempt, 60)  # Exponential backoff, max 60s
                print(f"  ⚠️  Rate limit hit (unexpected), waiting {wait_time}s...")
                time.sleep(wait_time)
                if attempt == MAX_RETRIES - 1:
                    print(f"  ❌ Rate limit exceeded after {MAX_RETRIES} attempts")
                    return {}
            except Exception as e:
                print(f"  ⚠️  Attempt {attempt + 1} failed: {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    print(f"  ❌ Failed after {MAX_RETRIES} attempts")
                    return {}
                # Small delay between retries
                time.sleep(1)
        
        return {}
    
    def _extract_processes(self, interview_text: str, meta: Dict) -> List[Dict]:
        """Extract processes from interview"""
        
        system_prompt = """Eres un analista de procesos empresariales.
Extrae los PROCESOS que el entrevistado describe en su trabajo diario.

Un proceso es:
- Una secuencia de pasos para lograr un resultado
- Una actividad recurrente con inputs y outputs
- Un flujo de trabajo que involucra sistemas o personas

Responde en JSON:
{
  "processes": [
    {
      "name": "Nombre del proceso",
      "owner": "Rol del entrevistado",
      "domain": "Finance|Operations|Maintenance|Sales|IT|HR|Logistics",
      "description": "Qué hace el proceso",
      "inputs": ["Input1", "Input2"],
      "outputs": ["Output1"],
      "systems": ["Sistema1", "Sistema2"],
      "frequency": "Hourly|Daily|Weekly|Monthly",
      "dependencies": ["Proceso o área de la que depende"]
    }
  ]
}"""
        
        result = self._call_gpt4(system_prompt, interview_text)
        processes = result.get("processes", [])
        print(f"  ✓ Processes: {len(processes)}")
        return processes
    
    def _extract_kpis(self, interview_text: str, meta: Dict) -> List[Dict]:
        """Extract KPIs from interview"""
        
        system_prompt = """Eres un analista de métricas empresariales.
Extrae los KPIs (indicadores) que el entrevistado usa para medir su éxito.

Un KPI es:
- Una métrica específica que se mide regularmente
- Un objetivo cuantificable
- Un indicador de desempeño

Responde en JSON:
{
  "kpis": [
    {
      "name": "Nombre del KPI",
      "domain": "Área",
      "definition": "Qué mide",
      "formula": "Cómo se calcula (si se menciona)",
      "owner": "Quién lo mide",
      "data_source": "De dónde viene el dato",
      "baseline": "Valor actual (si se menciona)",
      "target": "Meta (si se menciona)",
      "cadence": "hourly|daily|weekly|monthly|quarterly|annual",
      "related_processes": ["Procesos relacionados"]
    }
  ]
}"""
        
        result = self._call_gpt4(system_prompt, interview_text)
        kpis = result.get("kpis", [])
        print(f"  ✓ KPIs: {len(kpis)}")
        return kpis
    
    def _extract_inefficiencies(self, interview_text: str, meta: Dict) -> List[Dict]:
        """Extract inefficiencies from interview"""
        
        system_prompt = """Eres un analista de eficiencia operacional.
Extrae INEFICIENCIAS que el entrevistado menciona explícitamente.

Una ineficiencia es:
- Trabajo redundante o duplicado
- Pasos innecesarios en un proceso
- Tiempo perdido esperando aprobaciones
- Falta de información o comunicación

Responde en JSON:
{
  "inefficiencies": [
    {
      "description": "Descripción de la ineficiencia",
      "category": "Manual work|Waiting time|Rework|Communication|Approval delays",
      "frequency": "Daily|Weekly|Monthly",
      "time_wasted": "Estimado de tiempo perdido",
      "related_process": "Proceso afectado"
    }
  ]
}"""
        
        result = self._call_gpt4(system_prompt, interview_text)
        inefficiencies = result.get("inefficiencies", [])
        print(f"  ✓ Inefficiencies: {len(inefficiencies)}")
        return inefficiencies

    # ------------------------------------------------------------------ #
    # v2.0 → Legacy projections (compatibility during migration)
    # ------------------------------------------------------------------ #

    def _project_v2_entities(self, results: Dict[str, List[Dict]]) -> None:
        """
        Populate legacy entity keys using richer v2.0 structures so callers
        depending on v1 schemas continue to work during the migration.
        """
        results["pain_points"] = self._project_pain_points_from_v2(
            results.get("pain_points_v2", [])
        )
        results["systems"] = self._project_systems_from_v2(
            results.get("systems_v2", [])
        )
        results["automation_candidates"] = self._project_automation_from_v2(
            results.get("automation_candidates_v2", [])
        )

    def _project_pain_points_from_v2(self, pain_points_v2: List[Dict]) -> List[Dict]:
        """Map enhanced pain points into the legacy schema."""
        projected = []

        for pain in pain_points_v2 or []:
            projected.append({
                "type": pain.get("type", "Process Inefficiency"),
                "description": pain.get("description", ""),
                "affected_roles": pain.get("affected_roles", []),
                "affected_processes": pain.get("affected_processes", []),
                "frequency": pain.get("frequency", "Ad-hoc"),
                "severity": pain.get("severity", "Medium"),
                "impact_description": pain.get("impact_description", ""),
                "proposed_solutions": pain.get("proposed_solutions", []),
                "jtbd_who": pain.get("jtbd_who"),
                "jtbd_what": pain.get("jtbd_what"),
                "jtbd_where": pain.get("jtbd_where"),
                "time_wasted": pain.get("time_wasted_per_occurrence_minutes"),
                "root_cause": pain.get("root_cause"),
                "current_workaround": pain.get("current_workaround"),
                "hair_on_fire": pain.get("hair_on_fire", False),
                "confidence_score": pain.get("confidence_score", 0.0),
                "extraction_source": "v2_projection",
                "extraction_reasoning": pain.get("extraction_reasoning", "")
            })

        return projected

    def _project_systems_from_v2(self, systems_v2: List[Dict]) -> List[Dict]:
        """Map enhanced systems into the legacy schema."""
        projected: List[Dict[str, Any]] = []

        for system in systems_v2 or []:
            name = system.get("name")
            if not name:
                continue

            projected.append({
                "name": name,
                "domain": system.get("domain") or system.get("primary_use_case", "Unknown"),
                "vendor": system.get("vendor"),
                "type": system.get("type", system.get("system_type", "Other")),
                "pain_points": system.get("integration_pain_points", []),
                "data_quality_issues": system.get("data_quality_issues", []),
                "user_satisfaction_score": system.get("user_satisfaction_score", 5.0),
                "replacement_candidate": system.get("replacement_candidate", False),
                "adoption_rate": system.get("adoption_rate"),
                "extraction_source": "v2_projection",
                "extraction_reasoning": system.get("extraction_reasoning", "")
            })

        return projected

    def _project_automation_from_v2(self, automation_v2: List[Dict]) -> List[Dict]:
        """Map enhanced automation candidates into the legacy schema."""
        projected: List[Dict[str, Any]] = []

        for candidate in automation_v2 or []:
            projected.append({
                "name": candidate.get("name", candidate.get("process", "Automatización propuesta")),
                "process": candidate.get("process", ""),
                "trigger": candidate.get("trigger_event"),
                "action": candidate.get("action"),
                "output": candidate.get("output"),
                "owner": candidate.get("owner"),
                "complexity": candidate.get("complexity", "Medium"),
                "impact": candidate.get("impact", "Medium"),
                "effort_estimate": candidate.get("effort_estimate"),
                "systems_involved": candidate.get("systems_involved", []),
                "current_manual_process_description": candidate.get("current_manual_process_description"),
                "confidence_score": candidate.get("confidence_score", 0.0),
                "frequency": candidate.get("frequency"),
                "extraction_source": "v2_projection",
                "extraction_reasoning": candidate.get("extraction_reasoning", "")
            })

        return projected
