"""
AI-powered extraction of structured intelligence from interview responses
Uses GPT-4 to extract entities based on PHASE1_ONTOLOGY_SCHEMA.json
Orchestrates v1.0 and v2.0 extractors for all 17 entity types
"""
import json
from typing import Dict, List, Any
from openai import OpenAI
from .config import OPENAI_API_KEY, MODEL, TEMPERATURE, MAX_RETRIES

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
        print("  📦 Running v1.0 extractors...")
        results["pain_points"] = self._extract_pain_points(interview_text, meta)
        results["processes"] = self._extract_processes(interview_text, meta)
        results["systems"] = self._extract_systems(interview_text, meta)
        results["kpis"] = self._extract_kpis(interview_text, meta)
        results["automation_candidates"] = self._extract_automation_candidates(interview_text, meta)
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
        """Call GPT-4 with retry logic"""
        
        for attempt in range(MAX_RETRIES):
            try:
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
                
            except Exception as e:
                print(f"  ⚠️  Attempt {attempt + 1} failed: {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    print(f"  ❌ Failed after {MAX_RETRIES} attempts")
                    return {}
        
        return {}
    
    def _extract_pain_points(self, interview_text: str, meta: Dict) -> List[Dict]:
        """Extract pain points from interview"""
        
        system_prompt = """Eres un analista experto en procesos empresariales. 
Tu tarea es extraer PAIN POINTS (puntos de dolor/problemas) de entrevistas a gerentes.

Un pain point es:
- Un problema recurrente que dificulta el trabajo
- Una ineficiencia que causa frustración
- Un obstáculo que impide cumplir objetivos
- Una limitación de sistemas o procesos

Extrae SOLO pain points EXPLÍCITOS mencionados por el entrevistado.

Responde en JSON con este formato:
{
  "pain_points": [
    {
      "type": "Process|Data|Systems|Culture|Training|Approval|Integration",
      "description": "Descripción clara del problema",
      "affected_roles": ["Rol1", "Rol2"],
      "affected_processes": ["Proceso1"],
      "frequency": "Daily|Weekly|Monthly|Occasional",
      "severity": "Low|Medium|High|Critical",
      "impact_description": "Cómo afecta al trabajo",
      "proposed_solutions": ["Solución sugerida por el entrevistado"]
    }
  ]
}"""
        
        result = self._call_gpt4(system_prompt, interview_text)
        pain_points = result.get("pain_points", [])
        print(f"  ✓ Pain points: {len(pain_points)}")
        return pain_points
    
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
    
    def _extract_systems(self, interview_text: str, meta: Dict) -> List[Dict]:
        """Extract systems/tools from interview"""
        
        system_prompt = """Eres un analista de sistemas empresariales.
Extrae TODOS los sistemas, herramientas y software que el entrevistado menciona.

Incluye:
- Software empresarial (ERP, PMS, CRM, etc.)
- Herramientas de productividad (Excel, Outlook, etc.)
- Sistemas específicos del negocio
- Plataformas de comunicación

Responde en JSON:
{
  "systems": [
    {
      "name": "Nombre exacto del sistema",
      "domain": "Área de uso",
      "vendor": "Proveedor si se menciona",
      "type": "ERP|PMS|POS|CRM|CMMS|BI|Productivity|Communication",
      "pain_points": ["Problemas mencionados con este sistema"]
    }
  ]
}"""
        
        result = self._call_gpt4(system_prompt, interview_text)
        systems = result.get("systems", [])
        print(f"  ✓ Systems: {len(systems)}")
        return systems
    
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
    
    def _extract_automation_candidates(self, interview_text: str, meta: Dict) -> List[Dict]:
        """Extract automation opportunities from interview"""
        
        system_prompt = """Eres un experto en automatización de procesos.
Identifica oportunidades de AUTOMATIZACIÓN basadas en lo que el entrevistado describe.

Una oportunidad de automatización es:
- Una tarea manual repetitiva
- Un proceso que requiere copiar datos entre sistemas
- Una aprobación que podría tener reglas automáticas
- Un reporte que se genera manualmente

Responde en JSON:
{
  "automation_candidates": [
    {
      "name": "Nombre de la automatización",
      "process": "Proceso a automatizar",
      "trigger": "Qué inicia la automatización",
      "action": "Qué haría automáticamente",
      "output": "Resultado esperado",
      "owner": "Quién se beneficia",
      "complexity": "Low|Medium|High",
      "impact": "Low|Medium|High|Critical",
      "effort_estimate": "Estimado en días/semanas",
      "systems_involved": ["Sistema1", "Sistema2"]
    }
  ]
}"""
        
        result = self._call_gpt4(system_prompt, interview_text)
        automations = result.get("automation_candidates", [])
        print(f"  ✓ Automation candidates: {len(automations)}")
        return automations
    
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
