"""
RAG Database Generator for Intelligence Capture System

Generates company-specific and holding-level RAG databases with:
- Rich entity context by traversing relationships
- Vector embeddings for semantic search
- Company-specific partitioning
- Natural language query interface
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import openai
from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.config import OPENAI_API_KEY, MODEL


@dataclass
class EntityContext:
    """Rich context for an entity with related information"""
    entity_id: int
    entity_type: str
    company: str
    business_unit: Optional[str]
    primary_text: str
    related_entities: Dict[str, List[Dict]]
    metadata: Dict[str, Any]
    full_context: str


class EntityContextBuilder:
    """
    Builds rich context for entities by traversing relationships
    
    Example for PainPoint:
    - Related Process
    - Related Systems
    - Related FailureModes
    - Related AutomationCandidates
    - Related CommunicationChannels
    - Related DecisionPoints
    """
    
    def __init__(self, db: EnhancedIntelligenceDB):
        self.db = db
        self.conn = db.conn
    
    def build_context(self, entity_type: str, entity_id: int, depth: int = 2) -> EntityContext:
        """
        Build rich context for an entity by traversing relationships
        
        Args:
            entity_type: Type of entity (e.g., 'pain_point', 'process')
            entity_id: ID of the entity
            depth: How many levels of relationships to traverse (1-3)
            
        Returns:
            EntityContext with full context and related entities
        """
        # Get the primary entity
        entity = self._get_entity(entity_type, entity_id)
        if not entity:
            raise ValueError(f"Entity {entity_type}:{entity_id} not found")
        
        # Build primary text
        primary_text = self._format_entity_text(entity_type, entity)
        
        # Get related entities
        related_entities = {}
        if depth >= 1:
            related_entities = self._get_related_entities(entity_type, entity, depth)
        
        # Build full context text
        full_context = self._build_full_context_text(
            entity_type, entity, primary_text, related_entities
        )
        
        # Extract metadata
        metadata = self._extract_metadata(entity_type, entity)
        
        return EntityContext(
            entity_id=entity_id,
            entity_type=entity_type,
            company=entity.get('company') or entity.get('company_name', 'Unknown'),
            business_unit=entity.get('business_unit'),
            primary_text=primary_text,
            related_entities=related_entities,
            metadata=metadata,
            full_context=full_context
        )
    
    def _get_entity(self, entity_type: str, entity_id: int) -> Optional[Dict]:
        """Fetch entity from database"""
        table_map = {
            'pain_point': 'pain_points',
            'process': 'processes',
            'system': 'systems',
            'kpi': 'kpis',
            'automation_candidate': 'automation_candidates',
            'inefficiency': 'inefficiencies',
            'communication_channel': 'communication_channels',
            'decision_point': 'decision_points',
            'data_flow': 'data_flows',
            'temporal_pattern': 'temporal_patterns',
            'failure_mode': 'failure_modes',
            'team_structure': 'team_structures',
            'knowledge_gap': 'knowledge_gaps',
            'success_pattern': 'success_patterns',
            'budget_constraint': 'budget_constraints',
            'external_dependency': 'external_dependencies'
        }
        
        table = table_map.get(entity_type)
        if not table:
            return None
        
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Convert to dict
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row))
    
    def _format_entity_text(self, entity_type: str, entity: Dict) -> str:
        """Format entity as natural language text"""
        
        if entity_type == 'pain_point':
            return self._format_pain_point(entity)
        elif entity_type == 'process':
            return self._format_process(entity)
        elif entity_type == 'system':
            return self._format_system(entity)
        elif entity_type == 'automation_candidate':
            return self._format_automation_candidate(entity)
        elif entity_type == 'communication_channel':
            return self._format_communication_channel(entity)
        elif entity_type == 'decision_point':
            return self._format_decision_point(entity)
        elif entity_type == 'data_flow':
            return self._format_data_flow(entity)
        elif entity_type == 'temporal_pattern':
            return self._format_temporal_pattern(entity)
        elif entity_type == 'failure_mode':
            return self._format_failure_mode(entity)
        else:
            # Generic formatting
            return json.dumps(entity, indent=2)
    
    def _format_pain_point(self, entity: Dict) -> str:
        """Format pain point as natural language"""
        text = f"Pain Point: {entity.get('description', 'N/A')}\n"
        text += f"Type: {entity.get('type', 'N/A')}\n"
        text += f"Severity: {entity.get('severity', 'N/A')}"
        
        if entity.get('intensity_score'):
            text += f" (Intensity: {entity['intensity_score']}/10)"
        
        text += f"\nFrequency: {entity.get('frequency', 'N/A')}\n"
        
        if entity.get('hair_on_fire'):
            text += "⚠️ HAIR-ON-FIRE PROBLEM (High intensity + High frequency)\n"
        
        if entity.get('affected_roles'):
            roles = json.loads(entity['affected_roles']) if isinstance(entity['affected_roles'], str) else entity['affected_roles']
            text += f"Affected Roles: {', '.join(roles)}\n"
        
        if entity.get('impact_description'):
            text += f"Impact: {entity['impact_description']}\n"
        
        if entity.get('jtbd_formatted'):
            text += f"\nJobs-To-Be-Done Context:\n{entity['jtbd_formatted']}\n"
        
        if entity.get('root_cause'):
            text += f"\nRoot Cause: {entity['root_cause']}\n"
        
        if entity.get('current_workaround'):
            text += f"Current Workaround: {entity['current_workaround']}\n"
        
        if entity.get('time_wasted_per_occurrence_minutes'):
            text += f"Time Wasted: {entity['time_wasted_per_occurrence_minutes']} minutes per occurrence\n"
        
        if entity.get('estimated_annual_cost_usd'):
            text += f"Estimated Annual Cost: ${entity['estimated_annual_cost_usd']:,.2f}\n"
        
        return text
    
    def _format_process(self, entity: Dict) -> str:
        """Format process as natural language"""
        text = f"Process: {entity.get('name', 'N/A')}\n"
        text += f"Owner: {entity.get('owner', 'N/A')}\n"
        
        if entity.get('domain'):
            text += f"Domain: {entity['domain']}\n"
        
        if entity.get('description'):
            text += f"Description: {entity['description']}\n"
        
        if entity.get('frequency'):
            text += f"Frequency: {entity['frequency']}\n"
        
        if entity.get('systems'):
            systems = json.loads(entity['systems']) if isinstance(entity['systems'], str) else entity['systems']
            text += f"Systems Used: {', '.join(systems)}\n"
        
        return text
    
    def _format_system(self, entity: Dict) -> str:
        """Format system as natural language"""
        text = f"System: {entity.get('name', 'N/A')}\n"
        
        if entity.get('vendor'):
            text += f"Vendor: {entity['vendor']}\n"
        
        if entity.get('type'):
            text += f"Type: {entity['type']}\n"
        
        if entity.get('user_satisfaction_score'):
            text += f"User Satisfaction: {entity['user_satisfaction_score']}/10\n"
        
        if entity.get('replacement_candidate'):
            text += "⚠️ REPLACEMENT CANDIDATE\n"
        
        if entity.get('integration_pain_points'):
            pain_points = json.loads(entity['integration_pain_points']) if isinstance(entity['integration_pain_points'], str) else entity['integration_pain_points']
            if pain_points:
                text += f"Integration Pain Points:\n"
                for pp in pain_points:
                    text += f"  - {pp}\n"
        
        return text
    
    def _format_automation_candidate(self, entity: Dict) -> str:
        """Format automation candidate as natural language"""
        text = f"Automation Opportunity: {entity.get('name', 'N/A')}\n"
        text += f"Process: {entity.get('process', 'N/A')}\n"
        
        if entity.get('priority_quadrant'):
            text += f"Priority: {entity['priority_quadrant']}\n"
        
        if entity.get('effort_score') and entity.get('impact_score'):
            text += f"Effort: {entity['effort_score']}/5, Impact: {entity['impact_score']}/5\n"
        
        if entity.get('estimated_roi_months'):
            text += f"Estimated ROI: {entity['estimated_roi_months']} months\n"
        
        if entity.get('estimated_annual_savings_usd'):
            text += f"Estimated Annual Savings: ${entity['estimated_annual_savings_usd']:,.2f}\n"
        
        if entity.get('current_manual_process_description'):
            text += f"\nCurrent Manual Process:\n{entity['current_manual_process_description']}\n"
        
        if entity.get('action'):
            text += f"\nProposed Automation:\n{entity['action']}\n"
        
        return text
    
    def _format_communication_channel(self, entity: Dict) -> str:
        """Format communication channel as natural language"""
        text = f"Communication Channel: {entity.get('channel_name', 'N/A')}\n"
        text += f"Purpose: {entity.get('purpose', 'N/A')}\n"
        text += f"Frequency: {entity.get('frequency', 'N/A')}\n"
        
        if entity.get('response_sla_minutes'):
            text += f"Response SLA: {entity['response_sla_minutes']} minutes\n"
        
        if entity.get('participants'):
            participants = json.loads(entity['participants']) if isinstance(entity['participants'], str) else entity['participants']
            text += f"Participants: {', '.join(participants)}\n"
        
        return text
    
    def _format_decision_point(self, entity: Dict) -> str:
        """Format decision point as natural language"""
        text = f"Decision Point: {entity.get('decision_type', 'N/A')}\n"
        text += f"Decision Maker: {entity.get('decision_maker_role', 'N/A')}\n"
        
        if entity.get('decision_criteria'):
            criteria = json.loads(entity['decision_criteria']) if isinstance(entity['decision_criteria'], str) else entity['decision_criteria']
            text += f"Decision Criteria:\n"
            for criterion in criteria:
                text += f"  - {criterion}\n"
        
        if entity.get('escalation_trigger'):
            text += f"Escalation Trigger: {entity['escalation_trigger']}\n"
            text += f"Escalate To: {entity.get('escalation_to_role', 'N/A')}\n"
        
        return text
    
    def _format_data_flow(self, entity: Dict) -> str:
        """Format data flow as natural language"""
        text = f"Data Flow: {entity.get('source_system', 'N/A')} → {entity.get('target_system', 'N/A')}\n"
        text += f"Data Type: {entity.get('data_type', 'N/A')}\n"
        text += f"Transfer Method: {entity.get('transfer_method', 'N/A')}\n"
        text += f"Frequency: {entity.get('transfer_frequency', 'N/A')}\n"
        
        if entity.get('data_quality_issues'):
            issues = json.loads(entity['data_quality_issues']) if isinstance(entity['data_quality_issues'], str) else entity['data_quality_issues']
            if issues:
                text += f"Data Quality Issues:\n"
                for issue in issues:
                    text += f"  - {issue}\n"
        
        return text
    
    def _format_temporal_pattern(self, entity: Dict) -> str:
        """Format temporal pattern as natural language"""
        text = f"Activity: {entity.get('activity_name', 'N/A')}\n"
        text += f"Frequency: {entity.get('frequency', 'N/A')}\n"
        
        if entity.get('time_of_day'):
            text += f"Time: {entity['time_of_day']}\n"
        
        if entity.get('duration_minutes'):
            text += f"Duration: {entity['duration_minutes']} minutes\n"
        
        return text
    
    def _format_failure_mode(self, entity: Dict) -> str:
        """Format failure mode as natural language"""
        text = f"Failure: {entity.get('failure_description', 'N/A')}\n"
        text += f"Frequency: {entity.get('frequency', 'N/A')}\n"
        text += f"Impact: {entity.get('impact_description', 'N/A')}\n"
        
        if entity.get('root_cause'):
            text += f"Root Cause: {entity['root_cause']}\n"
        
        if entity.get('current_workaround'):
            text += f"Current Workaround: {entity['current_workaround']}\n"
        
        if entity.get('proposed_prevention'):
            text += f"Proposed Prevention: {entity['proposed_prevention']}\n"
        
        return text

    
    def _get_related_entities(self, entity_type: str, entity: Dict, depth: int) -> Dict[str, List[Dict]]:
        """
        Get related entities based on entity type and relationships
        
        Returns dict with keys like 'processes', 'systems', 'automation_candidates', etc.
        """
        related = {}
        
        if entity_type == 'pain_point':
            related = self._get_pain_point_relationships(entity, depth)
        elif entity_type == 'process':
            related = self._get_process_relationships(entity, depth)
        elif entity_type == 'system':
            related = self._get_system_relationships(entity, depth)
        elif entity_type == 'automation_candidate':
            related = self._get_automation_candidate_relationships(entity, depth)
        elif entity_type == 'communication_channel':
            related = self._get_communication_channel_relationships(entity, depth)
        elif entity_type == 'decision_point':
            related = self._get_decision_point_relationships(entity, depth)
        elif entity_type == 'data_flow':
            related = self._get_data_flow_relationships(entity, depth)
        elif entity_type == 'failure_mode':
            related = self._get_failure_mode_relationships(entity, depth)
        
        return related
    
    def _get_pain_point_relationships(self, entity: Dict, depth: int) -> Dict[str, List[Dict]]:
        """Get relationships for a pain point"""
        related = {}
        cursor = self.conn.cursor()
        
        # Get related processes (by name match in affected_processes)
        if entity.get('affected_processes'):
            affected_processes = json.loads(entity['affected_processes']) if isinstance(entity['affected_processes'], str) else entity['affected_processes']
            if affected_processes:
                placeholders = ','.join(['?' for _ in affected_processes])
                cursor.execute(f"SELECT * FROM processes WHERE name IN ({placeholders})", affected_processes)
                related['processes'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        # Get related automation candidates (same company and process)
        company = entity.get('company') or entity.get('company_name')
        if company:
            cursor.execute("""
                SELECT * FROM automation_candidates 
                WHERE company = ? 
                LIMIT 5
            """, (company,))
            related['automation_candidates'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        # Get related failure modes (same company)
        if company:
            cursor.execute("""
                SELECT * FROM failure_modes 
                WHERE company_name = ?
                LIMIT 5
            """, (company,))
            related['failure_modes'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        return related
    
    def _get_process_relationships(self, entity: Dict, depth: int) -> Dict[str, List[Dict]]:
        """Get relationships for a process"""
        related = {}
        cursor = self.conn.cursor()
        
        # Get related pain points
        process_name = entity.get('name')
        if process_name:
            cursor.execute("""
                SELECT * FROM pain_points 
                WHERE affected_processes LIKE ?
                LIMIT 10
            """, (f'%{process_name}%',))
            related['pain_points'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        # Get related systems
        if entity.get('systems'):
            systems = json.loads(entity['systems']) if isinstance(entity['systems'], str) else entity['systems']
            if systems:
                placeholders = ','.join(['?' for _ in systems])
                cursor.execute(f"SELECT * FROM systems WHERE name IN ({placeholders})", systems)
                related['systems'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        # Get related communication channels
        company = entity.get('company') or entity.get('company_name')
        if company:
            cursor.execute("""
                SELECT * FROM communication_channels 
                WHERE company_name = ?
                LIMIT 5
            """, (company,))
            related['communication_channels'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        # Get related decision points
        if company:
            cursor.execute("""
                SELECT * FROM decision_points 
                WHERE company_name = ? AND related_process = ?
                LIMIT 5
            """, (company, process_name))
            related['decision_points'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        return related
    
    def _get_system_relationships(self, entity: Dict, depth: int) -> Dict[str, List[Dict]]:
        """Get relationships for a system"""
        related = {}
        cursor = self.conn.cursor()
        
        system_name = entity.get('name')
        
        # Get processes using this system
        cursor.execute("""
            SELECT * FROM processes 
            WHERE systems LIKE ?
            LIMIT 10
        """, (f'%{system_name}%',))
        related['processes'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        # Get data flows involving this system
        cursor.execute("""
            SELECT * FROM data_flows 
            WHERE source_system = ? OR target_system = ?
            LIMIT 10
        """, (system_name, system_name))
        related['data_flows'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        # Get automation candidates involving this system
        cursor.execute("""
            SELECT * FROM automation_candidates 
            WHERE systems_involved LIKE ?
            LIMIT 10
        """, (f'%{system_name}%',))
        related['automation_candidates'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        return related
    
    def _get_automation_candidate_relationships(self, entity: Dict, depth: int) -> Dict[str, List[Dict]]:
        """Get relationships for an automation candidate"""
        related = {}
        cursor = self.conn.cursor()
        
        # Get related process
        process_name = entity.get('process')
        if process_name:
            cursor.execute("SELECT * FROM processes WHERE name = ? LIMIT 1", (process_name,))
            row = cursor.fetchone()
            if row:
                related['processes'] = [dict(zip([d[0] for d in cursor.description], row))]
        
        # Get related systems
        if entity.get('systems_involved'):
            systems = json.loads(entity['systems_involved']) if isinstance(entity['systems_involved'], str) else entity['systems_involved']
            if systems:
                placeholders = ','.join(['?' for _ in systems])
                cursor.execute(f"SELECT * FROM systems WHERE name IN ({placeholders})", systems)
                related['systems'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        # Get related failure modes
        if entity.get('id'):
            cursor.execute("""
                SELECT * FROM failure_modes 
                WHERE related_automation_candidate_id = ?
            """, (entity['id'],))
            related['failure_modes'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        return related
    
    def _get_communication_channel_relationships(self, entity: Dict, depth: int) -> Dict[str, List[Dict]]:
        """Get relationships for a communication channel"""
        related = {}
        cursor = self.conn.cursor()
        
        # Get related processes
        if entity.get('related_processes'):
            processes = json.loads(entity['related_processes']) if isinstance(entity['related_processes'], str) else entity['related_processes']
            if processes:
                placeholders = ','.join(['?' for _ in processes])
                cursor.execute(f"SELECT * FROM processes WHERE name IN ({placeholders})", processes)
                related['processes'] = [dict(zip([d[0] for d in cursor.description], row)) for row in cursor.fetchall()]
        
        return related
    
    def _get_decision_point_relationships(self, entity: Dict, depth: int) -> Dict[str, List[Dict]]:
        """Get relationships for a decision point"""
        related = {}
        cursor = self.conn.cursor()
        
        # Get related process
        process_name = entity.get('related_process')
        if process_name:
            cursor.execute("SELECT * FROM processes WHERE name = ? LIMIT 1", (process_name,))
            row = cursor.fetchone()
            if row:
                related['processes'] = [dict(zip([d[0] for d in cursor.description], row))]
        
        return related
    
    def _get_data_flow_relationships(self, entity: Dict, depth: int) -> Dict[str, List[Dict]]:
        """Get relationships for a data flow"""
        related = {}
        cursor = self.conn.cursor()
        
        # Get source and target systems
        source_system = entity.get('source_system')
        target_system = entity.get('target_system')
        
        if source_system:
            cursor.execute("SELECT * FROM systems WHERE name = ? LIMIT 1", (source_system,))
            row = cursor.fetchone()
            if row:
                related['source_systems'] = [dict(zip([d[0] for d in cursor.description], row))]
        
        if target_system:
            cursor.execute("SELECT * FROM systems WHERE name = ? LIMIT 1", (target_system,))
            row = cursor.fetchone()
            if row:
                related['target_systems'] = [dict(zip([d[0] for d in cursor.description], row))]
        
        # Get related process
        process_name = entity.get('related_process')
        if process_name:
            cursor.execute("SELECT * FROM processes WHERE name = ? LIMIT 1", (process_name,))
            row = cursor.fetchone()
            if row:
                related['processes'] = [dict(zip([d[0] for d in cursor.description], row))]
        
        return related
    
    def _get_failure_mode_relationships(self, entity: Dict, depth: int) -> Dict[str, List[Dict]]:
        """Get relationships for a failure mode"""
        related = {}
        cursor = self.conn.cursor()
        
        # Get related process
        process_name = entity.get('related_process')
        if process_name:
            cursor.execute("SELECT * FROM processes WHERE name = ? LIMIT 1", (process_name,))
            row = cursor.fetchone()
            if row:
                related['processes'] = [dict(zip([d[0] for d in cursor.description], row))]
        
        # Get related automation candidate
        if entity.get('related_automation_candidate_id'):
            cursor.execute("""
                SELECT * FROM automation_candidates 
                WHERE id = ?
            """, (entity['related_automation_candidate_id'],))
            row = cursor.fetchone()
            if row:
                related['automation_candidates'] = [dict(zip([d[0] for d in cursor.description], row))]
        
        return related
    
    def _build_full_context_text(
        self, 
        entity_type: str, 
        entity: Dict, 
        primary_text: str, 
        related_entities: Dict[str, List[Dict]]
    ) -> str:
        """Build complete context text including related entities"""
        
        # Start with company and business unit context
        company = entity.get('company') or entity.get('company_name', 'Unknown')
        business_unit = entity.get('business_unit', 'Unknown')
        
        context = f"Company: {company}\n"
        context += f"Business Unit: {business_unit}\n"
        context += f"\n{'='*60}\n\n"
        
        # Add primary entity
        context += primary_text
        context += f"\n{'='*60}\n"
        
        # Add related entities
        if related_entities:
            context += "\n## Related Information\n\n"
            
            for rel_type, entities in related_entities.items():
                if entities:
                    context += f"\n### Related {rel_type.replace('_', ' ').title()}\n\n"
                    for rel_entity in entities[:3]:  # Limit to 3 per type
                        rel_text = self._format_entity_text(
                            rel_type.rstrip('s'),  # Remove plural 's'
                            rel_entity
                        )
                        context += f"{rel_text}\n---\n"
        
        return context
    
    def _extract_metadata(self, entity_type: str, entity: Dict) -> Dict[str, Any]:
        """Extract metadata for filtering and retrieval"""
        metadata = {
            'entity_type': entity_type,
            'entity_id': entity.get('id'),
            'company': entity.get('company') or entity.get('company_name'),
            'business_unit': entity.get('business_unit'),
            'department': entity.get('department'),
            'created_at': entity.get('created_at'),
        }
        
        # Add entity-specific metadata
        if entity_type == 'pain_point':
            metadata.update({
                'severity': entity.get('severity'),
                'frequency': entity.get('frequency'),
                'intensity_score': entity.get('intensity_score'),
                'hair_on_fire': entity.get('hair_on_fire'),
                'estimated_annual_cost_usd': entity.get('estimated_annual_cost_usd'),
            })
        elif entity_type == 'automation_candidate':
            metadata.update({
                'priority_quadrant': entity.get('priority_quadrant'),
                'effort_score': entity.get('effort_score'),
                'impact_score': entity.get('impact_score'),
                'estimated_roi_months': entity.get('estimated_roi_months'),
                'ceo_priority': entity.get('ceo_priority'),
            })
        elif entity_type == 'system':
            metadata.update({
                'user_satisfaction_score': entity.get('user_satisfaction_score'),
                'replacement_candidate': entity.get('replacement_candidate'),
            })
        
        return metadata



class EmbeddingGenerator:
    """
    Generates vector embeddings for entity contexts using OpenAI's embedding model
    
    Uses text-embedding-3-small for cost-effective, high-quality embeddings
    """
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
        
        # Embedding dimensions for text-embedding-3-small
        self.embedding_dimensions = 1536
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process per API call (max 2048 for OpenAI)
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
                print(f"  Generated embeddings for batch {i//batch_size + 1} ({len(batch)} texts)")
                
            except Exception as e:
                print(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                raise
        
        return embeddings
    
    def generate_context_embedding(self, context: EntityContext) -> Tuple[List[float], Dict[str, Any]]:
        """
        Generate embedding for an EntityContext
        
        Args:
            context: EntityContext object with full_context text
            
        Returns:
            Tuple of (embedding vector, metadata dict)
        """
        # Generate embedding from full context
        embedding = self.generate_embedding(context.full_context)
        
        # Prepare metadata for storage
        metadata = {
            'entity_id': context.entity_id,
            'entity_type': context.entity_type,
            'company': context.company,
            'business_unit': context.business_unit,
            'text_length': len(context.full_context),
            **context.metadata  # Include entity-specific metadata
        }
        
        return embedding, metadata
    
    def estimate_cost(self, num_texts: int, avg_tokens_per_text: int = 500) -> float:
        """
        Estimate cost for generating embeddings
        
        text-embedding-3-small pricing: $0.02 per 1M tokens
        
        Args:
            num_texts: Number of texts to embed
            avg_tokens_per_text: Average tokens per text (rough estimate: 1 token ≈ 4 chars)
            
        Returns:
            Estimated cost in USD
        """
        total_tokens = num_texts * avg_tokens_per_text
        cost_per_million = 0.02
        estimated_cost = (total_tokens / 1_000_000) * cost_per_million
        
        return estimated_cost



@dataclass
class RAGDocument:
    """A document in the RAG database with embedding and metadata"""
    id: str
    entity_type: str
    entity_id: int
    company: str
    business_unit: Optional[str]
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]


class RAGDatabaseGenerator:
    """
    Generates company-specific and holding-level RAG databases
    
    Combines EntityContextBuilder and EmbeddingGenerator to create
    queryable vector databases for AI agents.
    """
    
    def __init__(self, db: EnhancedIntelligenceDB, api_key: str):
        self.db = db
        self.context_builder = EntityContextBuilder(db)
        self.embedding_generator = EmbeddingGenerator(api_key)
        self.documents: List[RAGDocument] = []
    
    def generate_documents_for_company(
        self, 
        company_name: str,
        entity_types: Optional[List[str]] = None,
        depth: int = 2
    ) -> List[RAGDocument]:
        """
        Generate RAG documents for all entities in a company
        
        Args:
            company_name: Name of company to generate documents for
            entity_types: List of entity types to include (None = all)
            depth: Relationship traversal depth
            
        Returns:
            List of RAGDocument objects
        """
        if entity_types is None:
            entity_types = [
                'pain_point', 'process', 'system', 'automation_candidate',
                'communication_channel', 'decision_point', 'data_flow',
                'temporal_pattern', 'failure_mode'
            ]
        
        documents = []
        
        print(f"\n🔨 Generating RAG documents for {company_name}...")
        
        for entity_type in entity_types:
            print(f"\n  Processing {entity_type}s...")
            
            # Query entities for this company
            try:
                entities = self.db.query_by_company(company_name, entity_type)
                
                if not entities:
                    print(f"    No {entity_type}s found")
                    continue
                
                print(f"    Found {len(entities)} {entity_type}s")
                
                # Build context and generate embeddings for each entity
                for entity in entities:
                    try:
                        # Build rich context
                        context = self.context_builder.build_context(
                            entity_type, 
                            entity['id'], 
                            depth=depth
                        )
                        
                        # Generate embedding
                        embedding, metadata = self.embedding_generator.generate_context_embedding(context)
                        
                        # Create RAG document
                        doc = RAGDocument(
                            id=f"{entity_type}_{entity['id']}",
                            entity_type=entity_type,
                            entity_id=entity['id'],
                            company=context.company,
                            business_unit=context.business_unit,
                            text=context.full_context,
                            embedding=embedding,
                            metadata=metadata
                        )
                        
                        documents.append(doc)
                        
                    except Exception as e:
                        print(f"    ⚠️  Error processing {entity_type} {entity['id']}: {e}")
                        continue
                
                print(f"    ✅ Generated {len([d for d in documents if d.entity_type == entity_type])} documents")
                
            except Exception as e:
                print(f"    ⚠️  Error querying {entity_type}s: {e}")
                continue
        
        print(f"\n✅ Generated {len(documents)} total documents for {company_name}")
        
        return documents
    
    def generate_documents_for_holding(
        self,
        entity_types: Optional[List[str]] = None,
        depth: int = 2
    ) -> List[RAGDocument]:
        """
        Generate RAG documents for all entities across all companies
        
        Args:
            entity_types: List of entity types to include (None = all)
            depth: Relationship traversal depth
            
        Returns:
            List of RAGDocument objects
        """
        companies = ["Hotel Los Tajibos", "Comversa", "Bolivian Foods"]
        
        all_documents = []
        
        print(f"\n🏢 Generating holding-level RAG database...")
        
        for company in companies:
            company_docs = self.generate_documents_for_company(
                company, 
                entity_types=entity_types,
                depth=depth
            )
            all_documents.extend(company_docs)
        
        print(f"\n✅ Generated {len(all_documents)} total documents for holding")
        
        return all_documents
    
    def save_documents(self, documents: List[RAGDocument], output_path: Path):
        """
        Save RAG documents to disk
        
        Saves as JSON with embeddings and metadata for later loading
        
        Args:
            documents: List of RAGDocument objects
            output_path: Path to save documents (will create .json file)
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert documents to serializable format
        docs_data = []
        for doc in documents:
            docs_data.append({
                'id': doc.id,
                'entity_type': doc.entity_type,
                'entity_id': doc.entity_id,
                'company': doc.company,
                'business_unit': doc.business_unit,
                'text': doc.text,
                'embedding': doc.embedding,
                'metadata': doc.metadata
            })
        
        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(docs_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved {len(documents)} documents to {output_path}")
        
        # Print statistics
        print(f"\n📊 Statistics:")
        print(f"  Total documents: {len(documents)}")
        print(f"  Total size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Count by entity type
        entity_counts = {}
        for doc in documents:
            entity_counts[doc.entity_type] = entity_counts.get(doc.entity_type, 0) + 1
        
        print(f"\n  By entity type:")
        for entity_type, count in sorted(entity_counts.items()):
            print(f"    {entity_type}: {count}")
    
    def load_documents(self, input_path: Path) -> List[RAGDocument]:
        """
        Load RAG documents from disk
        
        Args:
            input_path: Path to JSON file with documents
            
        Returns:
            List of RAGDocument objects
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            docs_data = json.load(f)
        
        documents = []
        for doc_data in docs_data:
            doc = RAGDocument(
                id=doc_data['id'],
                entity_type=doc_data['entity_type'],
                entity_id=doc_data['entity_id'],
                company=doc_data['company'],
                business_unit=doc_data['business_unit'],
                text=doc_data['text'],
                embedding=doc_data['embedding'],
                metadata=doc_data['metadata']
            )
            documents.append(doc)
        
        print(f"📂 Loaded {len(documents)} documents from {input_path}")
        
        return documents
    
    def estimate_generation_cost(self, company_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Estimate cost for generating RAG database
        
        Args:
            company_name: Company to estimate for (None = all companies)
            
        Returns:
            Dict with cost estimates
        """
        entity_types = [
            'pain_point', 'process', 'system', 'automation_candidate',
            'communication_channel', 'decision_point', 'data_flow',
            'temporal_pattern', 'failure_mode'
        ]
        
        total_entities = 0
        
        if company_name:
            companies = [company_name]
        else:
            companies = ["Hotel Los Tajibos", "Comversa", "Bolivian Foods"]
        
        for company in companies:
            for entity_type in entity_types:
                try:
                    entities = self.db.query_by_company(company, entity_type)
                    total_entities += len(entities)
                except:
                    continue
        
        # Estimate tokens (rough: 500 tokens per entity context)
        avg_tokens = 500
        estimated_cost = self.embedding_generator.estimate_cost(total_entities, avg_tokens)
        
        return {
            'total_entities': total_entities,
            'estimated_tokens': total_entities * avg_tokens,
            'estimated_cost_usd': estimated_cost,
            'companies': companies
        }


import numpy as np
from typing import Tuple


class CompanyRAGDatabase:
    """
    Company-specific RAG database with vector search capabilities
    
    Provides semantic search over company-specific entities using
    cosine similarity between embeddings.
    """
    
    def __init__(self, company_name: str, documents: List[RAGDocument]):
        self.company_name = company_name
        self.documents = documents
        
        # Build vector index
        self.embeddings_matrix = None
        self.document_ids = []
        self._build_index()
    
    def _build_index(self):
        """Build numpy matrix of embeddings for fast similarity search"""
        if not self.documents:
            print(f"⚠️  No documents to index for {self.company_name}")
            return
        
        # Convert embeddings to numpy matrix
        embeddings_list = [doc.embedding for doc in self.documents]
        self.embeddings_matrix = np.array(embeddings_list, dtype=np.float32)
        
        # Store document IDs for lookup
        self.document_ids = [doc.id for doc in self.documents]
        
        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(self.embeddings_matrix, axis=1, keepdims=True)
        self.embeddings_matrix = self.embeddings_matrix / norms
        
        print(f"📊 Built index for {self.company_name}: {len(self.documents)} documents")
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[RAGDocument, float]]:
        """
        Search for similar documents using cosine similarity
        
        Args:
            query_embedding: Query vector (1536 dimensions)
            top_k: Number of results to return
            filters: Optional filters (e.g., {'entity_type': 'pain_point'})
            
        Returns:
            List of (document, similarity_score) tuples, sorted by similarity
        """
        if self.embeddings_matrix is None or len(self.documents) == 0:
            return []
        
        # Apply filters first
        filtered_docs = self.documents
        filtered_indices = list(range(len(self.documents)))
        
        if filters:
            filtered_docs = []
            filtered_indices = []
            for i, doc in enumerate(self.documents):
                if self._matches_filters(doc, filters):
                    filtered_docs.append(doc)
                    filtered_indices.append(i)
        
        if not filtered_docs:
            return []
        
        # Get embeddings for filtered documents
        filtered_embeddings = self.embeddings_matrix[filtered_indices]
        
        # Normalize query embedding
        query_array = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_array)
        query_array = query_array / query_norm
        
        # Calculate cosine similarity
        similarities = np.dot(filtered_embeddings, query_array)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Return documents with scores
        results = []
        for idx in top_indices:
            doc = filtered_docs[idx]
            score = float(similarities[idx])
            results.append((doc, score))
        
        return results
    
    def _matches_filters(self, doc: RAGDocument, filters: Dict[str, Any]) -> bool:
        """Check if document matches filter criteria"""
        for key, value in filters.items():
            if key == 'entity_type' and doc.entity_type != value:
                return False
            elif key == 'business_unit' and doc.business_unit != value:
                return False
            elif key in doc.metadata and doc.metadata[key] != value:
                return False
        return True
    
    def get_by_id(self, doc_id: str) -> Optional[RAGDocument]:
        """Get document by ID"""
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None
    
    def get_by_entity(self, entity_type: str, entity_id: int) -> Optional[RAGDocument]:
        """Get document by entity type and ID"""
        doc_id = f"{entity_type}_{entity_id}"
        return self.get_by_id(doc_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {
            'company': self.company_name,
            'total_documents': len(self.documents),
            'entity_types': {},
            'business_units': {}
        }
        
        for doc in self.documents:
            # Count by entity type
            stats['entity_types'][doc.entity_type] = \
                stats['entity_types'].get(doc.entity_type, 0) + 1
            
            # Count by business unit
            if doc.business_unit:
                stats['business_units'][doc.business_unit] = \
                    stats['business_units'].get(doc.business_unit, 0) + 1
        
        return stats
    
    def save(self, output_path: Path):
        """Save RAG database to disk"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save documents as JSON
        docs_data = []
        for doc in self.documents:
            docs_data.append({
                'id': doc.id,
                'entity_type': doc.entity_type,
                'entity_id': doc.entity_id,
                'company': doc.company,
                'business_unit': doc.business_unit,
                'text': doc.text,
                'embedding': doc.embedding,
                'metadata': doc.metadata
            })
        
        data = {
            'company': self.company_name,
            'documents': docs_data,
            'statistics': self.get_statistics()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {self.company_name} RAG database to {output_path}")
        print(f"   {len(self.documents)} documents, {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    @classmethod
    def load(cls, input_path: Path) -> 'CompanyRAGDatabase':
        """Load RAG database from disk"""
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Reconstruct documents
        documents = []
        for doc_data in data['documents']:
            doc = RAGDocument(
                id=doc_data['id'],
                entity_type=doc_data['entity_type'],
                entity_id=doc_data['entity_id'],
                company=doc_data['company'],
                business_unit=doc_data['business_unit'],
                text=doc_data['text'],
                embedding=doc_data['embedding'],
                metadata=doc_data['metadata']
            )
            documents.append(doc)
        
        # Create database
        db = cls(data['company'], documents)
        
        print(f"📂 Loaded {db.company_name} RAG database from {input_path}")
        print(f"   {len(documents)} documents")
        
        return db


class HoldingRAGDatabase:
    """
    Holding-level RAG database aggregating all companies
    
    Provides cross-company search and aggregation capabilities.
    """
    
    def __init__(self, company_databases: Dict[str, CompanyRAGDatabase]):
        self.company_databases = company_databases
        
        # Aggregate all documents
        self.all_documents = []
        for company_db in company_databases.values():
            self.all_documents.extend(company_db.documents)
        
        # Build unified index
        self.embeddings_matrix = None
        self._build_index()
    
    def _build_index(self):
        """Build unified index across all companies"""
        if not self.all_documents:
            print("⚠️  No documents to index")
            return
        
        # Convert embeddings to numpy matrix
        embeddings_list = [doc.embedding for doc in self.all_documents]
        self.embeddings_matrix = np.array(embeddings_list, dtype=np.float32)
        
        # Normalize embeddings
        norms = np.linalg.norm(self.embeddings_matrix, axis=1, keepdims=True)
        self.embeddings_matrix = self.embeddings_matrix / norms
        
        print(f"📊 Built holding-level index: {len(self.all_documents)} documents across {len(self.company_databases)} companies")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        company_filter: Optional[str] = None
    ) -> List[Tuple[RAGDocument, float]]:
        """
        Search across all companies or filter by specific company
        
        Args:
            query_embedding: Query vector
            top_k: Number of results
            filters: Entity filters
            company_filter: Optional company name to filter by
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if company_filter:
            # Search specific company
            if company_filter in self.company_databases:
                return self.company_databases[company_filter].search(
                    query_embedding, top_k, filters
                )
            else:
                return []
        
        # Search across all companies
        if self.embeddings_matrix is None or len(self.all_documents) == 0:
            return []
        
        # Apply filters
        filtered_docs = self.all_documents
        filtered_indices = list(range(len(self.all_documents)))
        
        if filters:
            filtered_docs = []
            filtered_indices = []
            for i, doc in enumerate(self.all_documents):
                if self._matches_filters(doc, filters):
                    filtered_docs.append(doc)
                    filtered_indices.append(i)
        
        if not filtered_docs:
            return []
        
        # Get embeddings for filtered documents
        filtered_embeddings = self.embeddings_matrix[filtered_indices]
        
        # Normalize query
        query_array = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_array)
        query_array = query_array / query_norm
        
        # Calculate similarities
        similarities = np.dot(filtered_embeddings, query_array)
        
        # Get top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            doc = filtered_docs[idx]
            score = float(similarities[idx])
            results.append((doc, score))
        
        return results
    
    def _matches_filters(self, doc: RAGDocument, filters: Dict[str, Any]) -> bool:
        """Check if document matches filters"""
        for key, value in filters.items():
            if key == 'entity_type' and doc.entity_type != value:
                return False
            elif key == 'business_unit' and doc.business_unit != value:
                return False
            elif key == 'company' and doc.company != value:
                return False
            elif key in doc.metadata and doc.metadata[key] != value:
                return False
        return True
    
    def get_cross_company_insights(self, entity_type: str) -> Dict[str, Any]:
        """Get insights comparing entities across companies"""
        insights = {
            'entity_type': entity_type,
            'by_company': {}
        }
        
        for company, db in self.company_databases.items():
            company_docs = [d for d in db.documents if d.entity_type == entity_type]
            insights['by_company'][company] = {
                'count': len(company_docs),
                'documents': company_docs
            }
        
        return insights
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get holding-level statistics"""
        stats = {
            'total_documents': len(self.all_documents),
            'companies': {},
            'entity_types': {},
            'business_units': {}
        }
        
        # Aggregate by company
        for company, db in self.company_databases.items():
            stats['companies'][company] = db.get_statistics()
        
        # Aggregate entity types
        for doc in self.all_documents:
            stats['entity_types'][doc.entity_type] = \
                stats['entity_types'].get(doc.entity_type, 0) + 1
            
            if doc.business_unit:
                stats['business_units'][doc.business_unit] = \
                    stats['business_units'].get(doc.business_unit, 0) + 1
        
        return stats
    
    def save(self, output_dir: Path):
        """Save holding database (saves each company separately)"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save each company database
        for company, db in self.company_databases.items():
            company_filename = company.lower().replace(' ', '_') + '_rag.json'
            company_path = output_dir / company_filename
            db.save(company_path)
        
        # Save holding-level metadata
        metadata = {
            'companies': list(self.company_databases.keys()),
            'statistics': self.get_statistics()
        }
        
        metadata_path = output_dir / 'holding_metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved holding-level RAG database to {output_dir}")
    
    @classmethod
    def load(cls, input_dir: Path) -> 'HoldingRAGDatabase':
        """Load holding database from directory"""
        # Load metadata
        metadata_path = input_dir / 'holding_metadata.json'
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Load each company database
        company_databases = {}
        for company in metadata['companies']:
            company_filename = company.lower().replace(' ', '_') + '_rag.json'
            company_path = input_dir / company_filename
            
            if company_path.exists():
                company_db = CompanyRAGDatabase.load(company_path)
                company_databases[company] = company_db
        
        # Create holding database
        holding_db = cls(company_databases)
        
        print(f"\n📂 Loaded holding-level RAG database from {input_dir}")
        
        return holding_db



# Add methods to RAGDatabaseGenerator class
def _add_rag_creation_methods():
    """Helper to add RAG creation methods to RAGDatabaseGenerator"""
    pass

# Extend RAGDatabaseGenerator with company and holding RAG creation
RAGDatabaseGenerator.generate_company_rag = lambda self, company_name: self._generate_company_rag_impl(company_name)
RAGDatabaseGenerator.generate_holding_rag = lambda self: self._generate_holding_rag_impl()

def _generate_company_rag_impl(self, company_name: str, output_path: Optional[Path] = None) -> CompanyRAGDatabase:
    """
    Generate company-specific RAG database
    
    Args:
        company_name: Name of company
        output_path: Optional path to save database
        
    Returns:
        CompanyRAGDatabase instance
    """
    print(f"\n🏢 Generating RAG database for {company_name}...")
    
    # Generate documents
    documents = self.generate_documents_for_company(company_name, depth=2)
    
    # Create RAG database
    rag_db = CompanyRAGDatabase(company_name, documents)
    
    # Save if path provided
    if output_path:
        rag_db.save(output_path)
    
    return rag_db

def _generate_holding_rag_impl(self, output_dir: Optional[Path] = None) -> HoldingRAGDatabase:
    """
    Generate holding-level RAG database
    
    Args:
        output_dir: Optional directory to save databases
        
    Returns:
        HoldingRAGDatabase instance
    """
    print(f"\n🏢 Generating holding-level RAG database...")
    
    companies = ["Hotel Los Tajibos", "Comversa", "Bolivian Foods"]
    company_databases = {}
    
    for company in companies:
        # Generate company RAG
        company_db = self._generate_company_rag_impl(company)
        company_databases[company] = company_db
    
    # Create holding database
    holding_db = HoldingRAGDatabase(company_databases)
    
    # Save if path provided
    if output_dir:
        holding_db.save(output_dir)
    
    return holding_db

# Bind methods to class
RAGDatabaseGenerator._generate_company_rag_impl = _generate_company_rag_impl
RAGDatabaseGenerator._generate_holding_rag_impl = _generate_holding_rag_impl
