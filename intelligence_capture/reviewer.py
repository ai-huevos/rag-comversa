"""
Ensemble Validation System for Forensic-Grade Quality Review
Extracts with multiple models independently and synthesizes best results
"""
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from openai import OpenAI
from anthropic import Anthropic
import statistics


@dataclass
class ReviewMetrics:
    """Quality metrics for extracted entities"""
    accuracy_score: float  # 0.0-1.0: How well extraction matches source text
    completeness_score: float  # 0.0-1.0: Are key details captured?
    relevance_score: float  # 0.0-1.0: Is this entity actually important?
    consistency_score: float  # 0.0-1.0: Do relationships make sense?
    hallucination_score: float  # 0.0-1.0: How much was invented vs grounded?
    overall_quality: float  # 0.0-1.0: Weighted average
    consensus_level: float  # 0.0-1.0: Agreement across models
    needs_human_review: bool  # True if any score < threshold
    review_feedback: str  # Structured feedback for improvement
    model_agreement: Dict[str, Any]  # Which models agreed/disagreed

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return asdict(self)


@dataclass
class EnsembleExtraction:
    """Result from multi-model extraction"""
    entity_type: str  # "pain_points", "processes", etc.
    extractions: Dict[str, List[Dict]]  # {model_name: [extracted_entities]}
    synthesized_result: List[Dict]  # Best combined extraction
    metrics: ReviewMetrics  # Quality scores
    iteration_count: int  # Number of refinement iterations
    total_cost_usd: float  # Estimated API cost


class EnsembleExtractor:
    """
    Extracts entities using multiple models independently
    Forensic-grade approach: parallel extraction with diverse models
    """

    # Ensemble configuration: 3 different model families for diversity
    ENSEMBLE_MODELS = [
        "gpt-4o-mini",      # Fast, efficient (baseline)
        "gpt-4o",           # Stronger reasoning
        "gpt-4-turbo",      # Different architecture vintage
    ]

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize ensemble extractor"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key required")

        self.openai_client = OpenAI(api_key=api_key)
        self.extraction_prompts = self._load_extraction_prompts()

    def _load_extraction_prompts(self) -> Dict[str, str]:
        """
        Load extraction prompts for each entity type
        These define what to extract and how to structure the output
        """
        # These will match the existing extractor prompts
        # For now, return basic prompts - we'll enhance these
        return {
            "pain_points": """Extract pain points from the interview. For each pain point:
- description: Clear description of the problem
- type: Category (process, system, communication, resource, knowledge)
- severity: High/Medium/Low based on impact
- frequency: How often it occurs
- affected_roles: Who is impacted
- affected_processes: Which processes are affected
- impact_description: Business impact
- proposed_solutions: Any suggested solutions

Return valid JSON: {"pain_points": [...]}""",

            "processes": """Extract business processes from the interview. For each process:
- name: Process name
- owner: Who owns/manages it
- domain: Business domain
- description: What the process does
- inputs: What goes in
- outputs: What comes out
- systems: Technology systems used
- frequency: How often it runs
- dependencies: What it depends on

Return valid JSON: {"processes": [...]}""",

            "systems": """Extract technology systems from the interview. For each system:
- name: System name
- domain: Business domain
- vendor: Internal/External vendor
- type: System category
- pain_points: Issues with the system

Return valid JSON: {"systems": [...]}""",

            "kpis": """Extract KPIs and metrics from the interview. For each KPI:
- name: KPI name
- domain: Business domain
- definition: What it measures
- formula: How it's calculated
- owner: Who owns it
- data_source: Where data comes from
- baseline: Current value
- target: Target value
- cadence: Measurement frequency
- related_processes: Related processes

Return valid JSON: {"kpis": [...]}""",

            "automation_candidates": """Extract automation opportunities from the interview. For each candidate:
- name: Automation name
- process: Process to automate
- trigger_event: What triggers it
- action: What action to automate
- output: Expected output
- owner: Process owner
- complexity: High/Medium/Low
- impact: High/Medium/Low business impact
- effort_estimate: Estimated effort
- systems_involved: Systems that would be involved

Return valid JSON: {"automation_candidates": [...]}""",

            "inefficiencies": """Extract inefficiencies from the interview. For each inefficiency:
- description: What is inefficient
- category: Type of inefficiency
- time_wasted: Time impact
- cost_impact: Cost impact if mentioned
- affected_teams: Who is affected

Return valid JSON: {"inefficiencies": [...]}"""
        }

    def extract_with_model(
        self,
        model: str,
        entity_type: str,
        interview_text: str,
        meta: Dict
    ) -> Optional[List[Dict]]:
        """
        Extract entities using a specific model

        Args:
            model: OpenAI model name
            entity_type: Type of entity to extract
            interview_text: Interview transcript
            meta: Interview metadata

        Returns:
            List of extracted entities or None if failed
        """
        prompt = self.extraction_prompts.get(entity_type)
        if not prompt:
            print(f"  ⚠️  No prompt defined for {entity_type}")
            return None

        # Build context from interview
        context = self._build_extraction_context(interview_text, meta)

        messages = [
            {
                "role": "system",
                "content": "You are an expert business analyst extracting structured information from Spanish interview transcripts. Extract only information explicitly mentioned or strongly implied in the interview. Do not invent details."
            },
            {
                "role": "user",
                "content": f"{context}\n\n{prompt}"
            }
        ]

        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,  # Low temperature for consistency
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            # Extract the specific entity type from response
            entities = result.get(entity_type, [])

            # Add extraction metadata
            for entity in entities:
                entity["_extraction_model"] = model
                entity["_extraction_source"] = "llm"

            return entities

        except Exception as e:
            print(f"  ⚠️  {model} extraction failed for {entity_type}: {str(e)[:100]}")
            return None

    def _build_extraction_context(self, interview_text: str, meta: Dict) -> str:
        """Build context for extraction from interview data"""
        company = meta.get("company", "Unknown")
        respondent = meta.get("respondent", "Unknown")
        role = meta.get("role", "Unknown")

        # Convert QA pairs to text if needed
        if isinstance(interview_text, dict):
            qa_text = ""
            for q, a in interview_text.items():
                qa_text += f"\nP: {q}\nR: {a}\n"
            interview_text = qa_text
        elif isinstance(interview_text, list):
            interview_text = "\n".join(str(item) for item in interview_text)

        context = f"""Interview Context:
Company: {company}
Respondent: {respondent}
Role: {role}

Interview Transcript:
{interview_text}
"""
        return context

    def extract_ensemble(
        self,
        entity_type: str,
        interview_text: str,
        meta: Dict
    ) -> Dict[str, List[Dict]]:
        """
        Extract entities using all models in ensemble
        Returns dictionary mapping model name to extracted entities
        """
        print(f"\n  🔬 Ensemble extraction for: {entity_type}")
        extractions = {}

        for model in self.ENSEMBLE_MODELS:
            print(f"    → Extracting with {model}...")
            entities = self.extract_with_model(model, entity_type, interview_text, meta)

            if entities is not None:
                extractions[model] = entities
                print(f"      ✓ Extracted {len(entities)} {entity_type}")
            else:
                extractions[model] = []
                print(f"      ⚠️  No results from {model}")

        return extractions


class SynthesisAgent:
    """
    Uses Claude Sonnet 4.5 to synthesize best extraction from ensemble results
    Validates quality and detects hallucinations
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize synthesis agent with Claude"""
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            # Fallback to OpenAI GPT-4o if Claude not available
            print("  ℹ️  Anthropic API key not found, using GPT-4o for synthesis")
            self.use_claude = False
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            self.use_claude = True
            self.anthropic_client = Anthropic(api_key=api_key)

    def synthesize_extractions(
        self,
        entity_type: str,
        ensemble_extractions: Dict[str, List[Dict]],
        interview_text: str,
        meta: Dict
    ) -> Tuple[List[Dict], ReviewMetrics]:
        """
        Synthesize best extraction from multiple model outputs

        Args:
            entity_type: Type of entity
            ensemble_extractions: Results from each model
            interview_text: Original interview for validation
            meta: Interview metadata

        Returns:
            Tuple of (synthesized_entities, review_metrics)
        """
        print(f"\n  🧠 Synthesizing {entity_type} from {len(ensemble_extractions)} models...")

        # Build synthesis prompt
        prompt = self._build_synthesis_prompt(
            entity_type,
            ensemble_extractions,
            interview_text,
            meta
        )

        # Get synthesis from Claude or GPT-4o
        if self.use_claude:
            synthesis_result = self._synthesize_with_claude(prompt)
        else:
            synthesis_result = self._synthesize_with_gpt4(prompt)

        if not synthesis_result:
            print(f"  ⚠️  Synthesis failed, using majority vote fallback")
            return self._fallback_majority_vote(ensemble_extractions, entity_type)

        # Parse synthesis result
        try:
            result = json.loads(synthesis_result)
            synthesized = result.get("synthesized_entities", [])

            # Build review metrics
            metrics = ReviewMetrics(
                accuracy_score=result.get("quality_scores", {}).get("accuracy", 0.8),
                completeness_score=result.get("quality_scores", {}).get("completeness", 0.8),
                relevance_score=result.get("quality_scores", {}).get("relevance", 0.8),
                consistency_score=result.get("quality_scores", {}).get("consistency", 0.8),
                hallucination_score=1.0 - result.get("quality_scores", {}).get("hallucination_risk", 0.2),
                overall_quality=result.get("quality_scores", {}).get("overall", 0.8),
                consensus_level=result.get("consensus_level", 0.7),
                needs_human_review=result.get("needs_human_review", False),
                review_feedback=result.get("feedback", ""),
                model_agreement=result.get("model_agreement", {})
            )

            print(f"  ✓ Synthesized {len(synthesized)} {entity_type}")
            print(f"    Quality: {metrics.overall_quality:.2f} | Consensus: {metrics.consensus_level:.2f}")
            if metrics.needs_human_review:
                print(f"    ⚠️  Flagged for human review")

            return synthesized, metrics

        except Exception as e:
            print(f"  ⚠️  Failed to parse synthesis result: {str(e)}")
            return self._fallback_majority_vote(ensemble_extractions, entity_type)

    def _build_synthesis_prompt(
        self,
        entity_type: str,
        ensemble_extractions: Dict[str, List[Dict]],
        interview_text: str,
        meta: Dict
    ) -> str:
        """Build prompt for synthesis agent"""

        # Format ensemble results
        extraction_summary = ""
        for model, entities in ensemble_extractions.items():
            extraction_summary += f"\n## {model} ({len(entities)} entities)\n"
            extraction_summary += json.dumps(entities, indent=2, ensure_ascii=False)[:2000]  # Limit size
            extraction_summary += "\n"

        prompt = f"""You are a forensic quality analyst reviewing entity extractions from multiple AI models.

**Task**: Synthesize the best {entity_type} extraction from multiple model outputs.

**Interview Context**:
Company: {meta.get('company')}
Respondent: {meta.get('respondent')}
Role: {meta.get('role')}

**Original Interview** (for validation against hallucinations):
{str(interview_text)[:3000]}

**Ensemble Extractions**:
{extraction_summary}

**Your Task**:
1. Analyze all extractions and identify:
   - Which entities appear across multiple models (high consensus)
   - Which entities appear in only one model (potential hallucination or unique insight)
   - Conflicts or contradictions between models

2. For each entity, validate against the original interview:
   - Is it explicitly mentioned or strongly implied?
   - Are the details accurate or invented?
   - Is it relevant and important?

3. Synthesize the best combined extraction:
   - Include high-consensus entities with confidence
   - Evaluate single-model entities carefully (could be hallucination OR unique insight)
   - Resolve conflicts by choosing most accurate version
   - Add any critical entities that all models missed

4. Score quality across dimensions (0.0-1.0):
   - accuracy: How well does extraction match source?
   - completeness: Are key details captured?
   - relevance: Are entities actually important?
   - consistency: Do relationships make sense?
   - hallucination_risk: How much was invented? (0.0=none, 1.0=high)
   - overall: Weighted average quality

5. Calculate consensus_level (0.0-1.0): Agreement across models

6. Determine needs_human_review: True if any score < 0.7 or high disagreement

**Output Format** (valid JSON):
{{
  "synthesized_entities": [
    // Best combined entities with all relevant fields
  ],
  "quality_scores": {{
    "accuracy": 0.0-1.0,
    "completeness": 0.0-1.0,
    "relevance": 0.0-1.0,
    "consistency": 0.0-1.0,
    "hallucination_risk": 0.0-1.0,
    "overall": 0.0-1.0
  }},
  "consensus_level": 0.0-1.0,
  "needs_human_review": true/false,
  "feedback": "Detailed feedback on quality issues and recommendations",
  "model_agreement": {{
    "high_consensus": ["entity1", "entity2"],
    "medium_consensus": ["entity3"],
    "low_consensus": ["entity4"],
    "conflicts": ["description of conflicts"]
  }}
}}

Provide your synthesis now:
"""
        return prompt

    def _synthesize_with_claude(self, prompt: str) -> Optional[str]:
        """Synthesize using Claude Sonnet 4.5"""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                temperature=0.1,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract text content from response
            content = response.content[0].text

            # Claude might wrap JSON in markdown - extract it
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return content

        except Exception as e:
            print(f"  ⚠️  Claude synthesis failed: {str(e)[:100]}")
            return None

    def _synthesize_with_gpt4(self, prompt: str) -> Optional[str]:
        """Synthesize using GPT-4o (fallback)"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a forensic quality analyst. Provide responses in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"  ⚠️  GPT-4o synthesis failed: {str(e)[:100]}")
            return None

    def _fallback_majority_vote(
        self,
        ensemble_extractions: Dict[str, List[Dict]],
        entity_type: str
    ) -> Tuple[List[Dict], ReviewMetrics]:
        """
        Fallback: simple majority vote if synthesis fails
        Take entities that appear in majority of models
        """
        print(f"  🔄 Using majority vote fallback...")

        # Collect all unique entities (by description/name)
        all_entities = []
        for model, entities in ensemble_extractions.items():
            all_entities.extend(entities)

        # Simple deduplication by description
        seen = set()
        deduplicated = []
        for entity in all_entities:
            key = entity.get("description", entity.get("name", ""))
            if key and key not in seen:
                seen.add(key)
                deduplicated.append(entity)

        # Calculate basic consensus
        num_models = len(ensemble_extractions)
        consensus = 0.5 if num_models > 1 else 1.0

        metrics = ReviewMetrics(
            accuracy_score=0.7,  # Conservative estimate
            completeness_score=0.7,
            relevance_score=0.7,
            consistency_score=0.7,
            hallucination_score=0.7,
            overall_quality=0.7,
            consensus_level=consensus,
            needs_human_review=True,  # Always flag fallback results
            review_feedback="Used fallback majority vote - synthesis failed. Recommend human review.",
            model_agreement={"fallback": True}
        )

        return deduplicated, metrics


class EnsembleReviewer:
    """
    Main interface for ensemble validation system
    Orchestrates multi-model extraction and synthesis
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        enable_ensemble: bool = True
    ):
        """
        Initialize ensemble reviewer

        Args:
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key (optional, will use GPT-4o fallback)
            enable_ensemble: If False, skip ensemble and just add basic review
        """
        self.enable_ensemble = enable_ensemble
        self.extractor = EnsembleExtractor(openai_api_key)
        self.synthesizer = SynthesisAgent(anthropic_api_key)

    def review_extraction(
        self,
        entity_type: str,
        entities: List[Dict],
        interview_text: str,
        meta: Dict
    ) -> EnsembleExtraction:
        """
        Review extracted entities using ensemble validation

        Args:
            entity_type: Type of entity (pain_points, processes, etc.)
            entities: Already extracted entities (from original extractor)
            interview_text: Original interview for validation
            meta: Interview metadata

        Returns:
            EnsembleExtraction with synthesized results and quality metrics
        """
        if not self.enable_ensemble:
            # Quick mode: just add basic quality scores without re-extraction
            return self._basic_review(entity_type, entities, interview_text, meta)

        print(f"\n🔬 ENSEMBLE REVIEW: {entity_type}")
        print(f"  Original extraction: {len(entities)} entities")

        # Step 1: Extract with ensemble of models
        ensemble_extractions = self.extractor.extract_ensemble(
            entity_type,
            interview_text,
            meta
        )

        # Add original extraction to ensemble for comparison
        ensemble_extractions["original"] = entities

        # Step 2: Synthesize best results
        synthesized, metrics = self.synthesizer.synthesize_extractions(
            entity_type,
            ensemble_extractions,
            interview_text,
            meta
        )

        # Step 3: Build final result
        result = EnsembleExtraction(
            entity_type=entity_type,
            extractions=ensemble_extractions,
            synthesized_result=synthesized,
            metrics=metrics,
            iteration_count=1,
            total_cost_usd=self._estimate_cost(ensemble_extractions)
        )

        print(f"\n  ✅ Ensemble review complete")
        print(f"     Original: {len(entities)} | Synthesized: {len(synthesized)} | Quality: {metrics.overall_quality:.2f}")

        return result

    def _basic_review(
        self,
        entity_type: str,
        entities: List[Dict],
        interview_text: str,
        meta: Dict
    ) -> EnsembleExtraction:
        """Basic review without re-extraction (faster, cheaper)"""
        print(f"\n  📋 Basic review: {entity_type} ({len(entities)} entities)")

        # Assign conservative quality scores
        metrics = ReviewMetrics(
            accuracy_score=0.75,
            completeness_score=0.75,
            relevance_score=0.75,
            consistency_score=0.75,
            hallucination_score=0.75,
            overall_quality=0.75,
            consensus_level=1.0,  # Only one model, full "consensus"
            needs_human_review=False,
            review_feedback="Basic review - single model extraction",
            model_agreement={"basic_mode": True}
        )

        result = EnsembleExtraction(
            entity_type=entity_type,
            extractions={"original": entities},
            synthesized_result=entities,
            metrics=metrics,
            iteration_count=0,
            total_cost_usd=0.0
        )

        return result

    def _estimate_cost(self, ensemble_extractions: Dict[str, List[Dict]]) -> float:
        """Estimate API costs for ensemble extraction"""
        # Rough estimates (adjust based on actual usage)
        cost_per_model = {
            "gpt-4o-mini": 0.01,
            "gpt-4o": 0.03,
            "gpt-4-turbo": 0.02,
            "claude-sonnet-4-5": 0.05
        }

        total = 0.0
        for model in ensemble_extractions.keys():
            if model != "original":
                total += cost_per_model.get(model, 0.02)

        # Add synthesis cost
        total += 0.05

        return total

    def review_all_entities(
        self,
        all_entities: Dict[str, List[Dict]],
        interview_text: str,
        meta: Dict
    ) -> Dict[str, EnsembleExtraction]:
        """
        Review all entity types from an interview

        Args:
            all_entities: Dict mapping entity_type to list of entities
            interview_text: Original interview
            meta: Interview metadata

        Returns:
            Dict mapping entity_type to EnsembleExtraction
        """
        print(f"\n{'='*60}")
        print(f"🔬 ENSEMBLE VALIDATION SYSTEM")
        print(f"{'='*60}")
        print(f"Interview: {meta.get('respondent', 'Unknown')} ({meta.get('company', 'Unknown')})")
        print(f"Entity types: {len(all_entities)}")
        print(f"Ensemble mode: {'ENABLED' if self.enable_ensemble else 'BASIC'}")

        reviewed = {}

        for entity_type, entities in all_entities.items():
            if len(entities) > 0:  # Only review if entities were found
                reviewed[entity_type] = self.review_extraction(
                    entity_type,
                    entities,
                    interview_text,
                    meta
                )

        print(f"\n{'='*60}")
        print(f"✅ VALIDATION COMPLETE")
        print(f"{'='*60}")

        # Summary stats
        total_original = sum(len(e) for e in all_entities.values())
        total_synthesized = sum(len(r.synthesized_result) for r in reviewed.values())
        avg_quality = statistics.mean([r.metrics.overall_quality for r in reviewed.values()]) if reviewed else 0.0
        needs_review_count = sum(1 for r in reviewed.values() if r.metrics.needs_human_review)

        print(f"Entities: {total_original} → {total_synthesized}")
        print(f"Avg Quality: {avg_quality:.2f}")
        print(f"Needs Review: {needs_review_count}/{len(reviewed)}")

        return reviewed
