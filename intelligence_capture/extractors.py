"""
Entity extraction logic for v2.0 ontology
Extracts structured entities from interview transcripts
"""
import re
import json
import time
from typing import Dict, List, Optional, Tuple
from openai import OpenAI, RateLimitError
import os


# Model fallback chain - Optimized for structured extraction
# gpt-4o-mini is PERFECT for structured JSON extraction tasks
MODEL_FALLBACK_CHAIN = [
    "gpt-4o-mini",              # Primary: Best cost/quality for structured extraction
    "gpt-4o-mini",              # Retry: Rate limits are usually temporary
    "gpt-4o",                   # Last resort: Only if 4o-mini completely unavailable
]


def call_llm_with_fallback(client: OpenAI, messages: List[Dict], temperature: float = 0.1, max_retries: int = 3) -> Optional[str]:
    """
    Call LLM with automatic model fallback on rate limits
    
    Args:
        client: OpenAI client
        messages: List of message dicts
        temperature: Temperature for generation
        max_retries: Max retries per model
        
    Returns:
        Response content or None if all models fail
    """
    last_error = None
    
    for model in MODEL_FALLBACK_CHAIN:
        for attempt in range(max_retries):
            try:
                print(f"  Attempting with model: {model} (attempt {attempt + 1}/{max_retries})")
                
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"}
                )
                
                print(f"  ✓ Success with {model}")
                return response.choices[0].message.content
                
            except RateLimitError as e:
                last_error = e
                error_msg = str(e)
                
                # Check if it's a temporary rate limit (wait and retry same model)
                if "Please try again in" in error_msg and "s." in error_msg:
                    # Extract wait time if it's short (< 60 seconds)
                    try:
                        wait_match = re.search(r'try again in (\d+)s', error_msg)
                        if wait_match:
                            wait_seconds = int(wait_match.group(1))
                            if wait_seconds <= 60:
                                print(f"  ⏳ Rate limit hit, waiting {wait_seconds}s before retry...")
                                time.sleep(wait_seconds + 1)
                                continue
                    except:
                        pass
                
                # If it's a longer wait or different rate limit, try next model
                print(f"  ⚠️  Rate limit on {model}: {error_msg[:100]}...")
                print(f"  → Switching to next model in fallback chain")
                break  # Move to next model
                
            except Exception as e:
                last_error = e
                print(f"  ⚠️  Error with {model}: {str(e)[:100]}...")
                
                # For non-rate-limit errors, retry same model
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"  ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"  → Max retries reached for {model}, trying next model")
                    break
    
    # All models failed
    print(f"  ❌ All models in fallback chain failed")
    if last_error:
        print(f"  Last error: {str(last_error)[:200]}")
    
    return None


class CommunicationChannelExtractor:
    """Extracts communication channel entities from interview text"""
    
    # Known communication channels
    KNOWN_CHANNELS = [
        "WhatsApp", "Outlook", "Email", "Teams", "Slack", 
        "Phone", "Teléfono", "Reuniones", "Meetings",
        "Jira", "Trello", "Notion", "SharePoint"
    ]
    
    # SLA keywords and their minute equivalents
    SLA_MAPPINGS = {
        "inmediato": 15,
        "urgente": 30,
        "mismo día": 480,
        "24 horas": 1440,
        "mismo turno": 480,
        "en el momento": 15,
        "rápido": 60,
        "continuo": 0,  # Always on
    }
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract communication channels from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of communication channel entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text for analysis
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # First, do rule-based extraction for obvious mentions
        rule_based_channels = self._rule_based_extraction(full_text, meta)
        
        # Then, use LLM for deeper extraction
        llm_channels = self._llm_extraction(full_text, meta)
        
        # Merge and deduplicate
        all_channels = self._merge_channels(rule_based_channels, llm_channels)
        
        return all_channels
    
    def _rule_based_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Extract channels using pattern matching"""
        channels = []
        text_lower = text.lower()
        
        for channel in self.KNOWN_CHANNELS:
            if channel.lower() in text_lower:
                # Found a channel mention
                channel_data = {
                    "channel_name": channel,
                    "purpose": self._infer_purpose(text, channel),
                    "frequency": self._infer_frequency(text, channel),
                    "participants": [meta.get("role", "Unknown")],
                    "response_sla_minutes": self._extract_sla(text, channel),
                    "pain_points": self._extract_pain_points(text, channel),
                    "related_processes": [],
                    "confidence_score": 0.7,  # Rule-based has moderate confidence
                    "extraction_source": "rule_based",
                    "extraction_reasoning": f"Found explicit mention of {channel} in interview text"
                }
                channels.append(channel_data)
        
        return channels
    
    def _infer_purpose(self, text: str, channel: str) -> str:
        """Infer the purpose of using this channel"""
        text_lower = text.lower()
        channel_lower = channel.lower()
        
        # Look for context around channel mention
        pattern = rf"{channel_lower}[^.]*?(?:para|por|de|en)[^.]*?\."
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        
        if matches:
            # Extract the most informative match
            return matches[0].strip()
        
        # Default purposes based on channel type
        purpose_defaults = {
            "whatsapp": "Comunicación diaria y coordinación",
            "outlook": "Comunicación formal y solicitudes",
            "email": "Comunicación formal",
            "teams": "Colaboración y reuniones",
            "phone": "Comunicación urgente",
            "reuniones": "Coordinación y planificación",
            "jira": "Gestión de tickets y proyectos"
        }
        
        return purpose_defaults.get(channel_lower, "Comunicación general")
    
    def _infer_frequency(self, text: str, channel: str) -> str:
        """Infer how frequently the channel is used"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["continuo", "todo el tiempo", "siempre"]):
            return "Continuous"
        elif any(word in text_lower for word in ["diario", "cada día", "todos los días"]):
            return "Daily"
        elif any(word in text_lower for word in ["semanal", "cada semana"]):
            return "Weekly"
        elif any(word in text_lower for word in ["mensual", "cada mes"]):
            return "Monthly"
        else:
            return "As needed"
    
    def _extract_sla(self, text: str, channel: str) -> Optional[int]:
        """Extract response SLA in minutes"""
        text_lower = text.lower()
        
        for keyword, minutes in self.SLA_MAPPINGS.items():
            if keyword in text_lower:
                return minutes
        
        return None
    
    def _extract_pain_points(self, text: str, channel: str) -> List[str]:
        """Extract pain points related to this channel"""
        pain_points = []
        text_lower = text.lower()
        
        # Common pain point patterns
        pain_patterns = [
            "pérdida de trazabilidad",
            "información dispersa",
            "difícil hacer seguimiento",
            "no hay registro",
            "se pierde información",
            "falta de control",
            "desorganizado"
        ]
        
        for pattern in pain_patterns:
            if pattern in text_lower:
                pain_points.append(pattern.capitalize())
        
        return pain_points
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Use LLM to extract communication channels with deeper understanding"""
        
        if not self.client:
            # No API key available, skip LLM extraction
            return []
        
        prompt = f"""You are analyzing an interview to extract communication channels and collaboration tools. Focus on identifying HOW people communicate, coordinate, and share information.

**Interview Context:**
- Role: {meta.get('role', 'Unknown')}
- Company: {meta.get('company', 'Unknown')}

**Interview Text:**
{text[:4000]}

**Your Task:**
Extract ALL communication channels and collaboration tools mentioned. A communication channel exists when:
1. A tool or platform is used for communication (WhatsApp, Outlook, Teams, Slack, etc.)
2. A meeting or coordination mechanism is mentioned (reuniones, juntas, stand-ups)
3. A notification or alert system is described
4. An informal communication method is used (phone calls, in-person, walkie-talkies)

**Look for these patterns:**
- "Uso [channel] para [purpose]"
- "Nos comunicamos por [channel]"
- "Coordinamos mediante [channel]"
- "Recibo solicitudes por [channel]"
- "Tenemos reuniones [frequency]"
- "[Channel] es para [purpose]"
- "Me contactan por [channel]"

**For each communication channel, extract:**

1. **channel_name**: Name of the channel/tool (e.g., "WhatsApp", "Outlook", "Reuniones semanales", "Teams", "Jira")
2. **purpose**: Why they use this channel (e.g., "Solicitudes urgentes", "Comunicación formal", "Coordinación diaria", "Gestión de tickets")
3. **frequency**: How often it's used:
   - "Continuous" - always on, real-time
   - "Daily" - used every day
   - "Weekly" - used weekly
   - "Monthly" - used monthly
   - "As needed" - used when necessary
4. **participants**: Who uses this channel (roles/departments, e.g., ["Recepción", "Housekeeping", "Ingeniería"])
5. **response_sla_minutes**: Expected response time in minutes:
   - "inmediato" / "urgente" → 15 minutes
   - "mismo día" → 480 minutes (8 hours)
   - "24 horas" → 1440 minutes
   - null if not mentioned
6. **pain_points**: Specific problems with this channel (e.g., "Pérdida de trazabilidad", "Información dispersa", "Difícil hacer seguimiento")
7. **related_processes**: Business processes that use this channel (e.g., ["Gestión de mantenimiento", "Atención de quejas"])
8. **confidence_score**: 0.0-1.0 based on how explicit the mention is
9. **extraction_reasoning**: Brief explanation of why you extracted this

**Important Guidelines:**
- Include both digital tools (WhatsApp, Outlook) AND physical meetings (reuniones, juntas)
- Distinguish between formal and informal channels
- Extract specific purposes, not generic "comunicación"
- Identify pain points related to each channel (lost messages, no tracking, etc.)
- Note if multiple channels are used for the same purpose (redundancy)
- Extract SLA expectations when mentioned ("respondo inmediato", "mismo día")
- Be specific about participants (roles, not just "equipo")

**Examples of Communication Channels:**
- "Uso WhatsApp para urgencias, respondo inmediato" → WhatsApp channel with 15-minute SLA
- "Outlook es para solicitudes formales que pueden esperar" → Outlook for formal requests
- "Tenemos reuniones semanales de coordinación con todos los jefes" → Weekly coordination meetings
- "Jira para gestionar tickets de mantenimiento" → Jira for ticket management
- "Me llaman por teléfono cuando es crítico" → Phone for critical issues

**Return Format:**
{{
  "channels": [
    {{
      "channel_name": "Channel/tool name",
      "purpose": "Specific purpose",
      "frequency": "Continuous|Daily|Weekly|Monthly|As needed",
      "participants": ["Role 1", "Role 2"],
      "response_sla_minutes": number or null,
      "pain_points": ["Specific pain 1", "Specific pain 2"],
      "related_processes": ["Process 1", "Process 2"],
      "confidence_score": 0.0-1.0,
      "extraction_reasoning": "Brief explanation"
    }}
  ]
}}

If no communication channels are found, return {{"channels": []}}.
"""
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert in organizational communication analysis and collaboration tools. You extract structured information about how teams communicate, coordinate, and share information. Always return valid JSON."
                },
                {"role": "user", "content": prompt}
            ]
            
            response_content = call_llm_with_fallback(self.client, messages, temperature=0.1)
            
            if not response_content:
                print("Warning: All LLM models failed for communication channel extraction")
                return []
            
            result = json.loads(response_content)
            channels = result.get("channels", [])
            
            # Add extraction source and validate
            for channel in channels:
                channel["extraction_source"] = "llm_extraction"
                
                # Ensure required fields exist
                if not channel.get("channel_name"):
                    continue
                
                # Set defaults for missing fields
                channel.setdefault("purpose", "Comunicación general")
                channel.setdefault("frequency", "As needed")
                channel.setdefault("participants", [])
                channel.setdefault("response_sla_minutes", None)
                channel.setdefault("pain_points", [])
                channel.setdefault("related_processes", [])
                channel.setdefault("confidence_score", 0.8)
                channel.setdefault("extraction_reasoning", "Extracted by LLM")
            
            return channels
            
        except Exception as e:
            print(f"Warning: LLM extraction failed: {e}")
            return []
    
    def _merge_channels(self, rule_based: List[Dict], llm_based: List[Dict]) -> List[Dict]:
        """Merge and deduplicate channels from different extraction methods"""
        merged = {}
        
        # Add rule-based channels
        for channel in rule_based:
            key = channel["channel_name"].lower()
            merged[key] = channel
        
        # Merge LLM channels (prefer LLM data if confidence is higher)
        for channel in llm_based:
            key = channel["channel_name"].lower()
            if key in merged:
                # Merge: prefer higher confidence data
                if channel.get("confidence_score", 0) > merged[key].get("confidence_score", 0):
                    # Keep LLM data but merge pain points
                    existing_pain_points = set(merged[key].get("pain_points", []))
                    new_pain_points = set(channel.get("pain_points", []))
                    channel["pain_points"] = list(existing_pain_points | new_pain_points)
                    merged[key] = channel
            else:
                merged[key] = channel
        
        return list(merged.values())


def normalize_sla_to_minutes(sla_text: str) -> Optional[int]:
    """
    Normalize SLA text to minutes
    
    Examples:
        "15 minutos" -> 15
        "1 hora" -> 60
        "mismo día" -> 480
        "24 horas" -> 1440
    """
    if not sla_text:
        return None
    
    text_lower = sla_text.lower().strip()
    
    # Direct mappings
    mappings = {
        "inmediato": 15,
        "urgente": 30,
        "mismo día": 480,
        "24 horas": 1440,
        "48 horas": 2880,
        "1 semana": 10080,
        "continuo": 0,
    }
    
    if text_lower in mappings:
        return mappings[text_lower]
    
    # Extract numbers
    # "15 minutos" -> 15
    minutes_match = re.search(r'(\d+)\s*min', text_lower)
    if minutes_match:
        return int(minutes_match.group(1))
    
    # "2 horas" -> 120
    hours_match = re.search(r'(\d+)\s*hora', text_lower)
    if hours_match:
        return int(hours_match.group(1)) * 60
    
    # "3 días" -> 4320
    days_match = re.search(r'(\d+)\s*d[ií]a', text_lower)
    if days_match:
        return int(days_match.group(1)) * 1440
    
    return None


class SystemExtractor:
    """Extracts enhanced system entities with integration pain points and user satisfaction"""
    
    # Sentiment indicators for user satisfaction scoring
    POSITIVE_INDICATORS = {
        "me gusta": 8,
        "funciona bien": 8,
        "útil": 7,
        "fácil": 7,
        "rápido": 7,
        "confiable": 8,
        "bueno": 7,
        "excelente": 9,
        "perfecto": 9,
        "satisfecho": 8,
        "eficiente": 8
    }
    
    NEGATIVE_INDICATORS = {
        "no sirve": 2,
        "no funciona": 2,
        "malo": 3,
        "lento": 4,
        "complicado": 4,
        "difícil": 4,
        "problema": 3,
        "falla": 2,
        "se cae": 2,
        "no me gusta": 3,
        "frustrante": 3,
        "inútil": 2,
        "obsoleto": 3,
        "desactualizado": 3
    }
    
    # Known system names for extraction
    KNOWN_SYSTEMS = [
        "SAP", "Opera", "Simphony", "Micros", "Oracle", "Excel", "Outlook",
        "Teams", "WhatsApp", "Jira", "Trello", "Notion", "SharePoint",
        "QuickBooks", "Salesforce", "HubSpot", "Zendesk", "Slack"
    ]
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract enhanced system entities from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of enhanced system entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text for analysis
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # Extract systems using LLM
        systems = self._llm_extraction(full_text, meta)
        
        # Enhance each system with sentiment analysis
        for system in systems:
            system["user_satisfaction_score"] = self._analyze_sentiment(full_text, system["name"])
            system["replacement_candidate"] = system["user_satisfaction_score"] <= 3
            
        return systems
    
    def _analyze_sentiment(self, text: str, system_name: str) -> float:
        """
        Analyze user sentiment towards a specific system
        
        Returns:
            Satisfaction score from 1-10
        """
        text_lower = text.lower()
        system_lower = system_name.lower()
        
        # Find context around system mentions (broader context - up to 100 chars after mention)
        pattern = rf"{re.escape(system_lower)}.{{0,100}}"
        mentions = re.findall(pattern, text_lower, re.IGNORECASE)
        
        if not mentions:
            # Try finding system in broader context
            if system_lower in text_lower:
                # Get surrounding context (50 chars before and after)
                idx = text_lower.find(system_lower)
                start = max(0, idx - 50)
                end = min(len(text_lower), idx + len(system_lower) + 100)
                mentions = [text_lower[start:end]]
            else:
                return 5.0  # Neutral if no context
        
        # Analyze sentiment in mentions
        scores = []
        for mention in mentions:
            score = 5.0  # Start neutral
            
            # Check for positive indicators
            for indicator, value in self.POSITIVE_INDICATORS.items():
                if indicator in mention:
                    score = max(score, value)
            
            # Check for negative indicators
            for indicator, value in self.NEGATIVE_INDICATORS.items():
                if indicator in mention:
                    score = min(score, value)
            
            scores.append(score)
        
        # Return average score
        return sum(scores) / len(scores) if scores else 5.0
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Use LLM to extract systems with integration pain points and satisfaction"""
        
        if not self.client:
            return []
        
        prompt = f"""You are analyzing an interview to extract information about systems, software, and tools used in the organization. Focus on identifying integration issues, data quality problems, and user satisfaction.

**Interview Context:**
- Role: {meta.get('role', 'Unknown')}
- Company: {meta.get('company', 'Unknown')}

**Interview Text:**
{text[:4000]}

**Your Task:**
Extract ALL systems, software, and tools mentioned. A system exists when:
1. A software application is mentioned (SAP, Opera, Excel, etc.)
2. A platform or tool is used for work (Outlook, Teams, Jira, etc.)
3. A business system is referenced (ERP, PMS, POS, CRM, etc.)

**For each system, extract:**

1. **name**: Exact name of the system (e.g., "SAP", "Opera PMS", "Simphony POS", "Excel")
2. **domain**: Area of use (e.g., "Finance", "Operations", "Sales", "Inventory")
3. **vendor**: Vendor/provider if mentioned (e.g., "Oracle", "Microsoft", "Micros")
4. **type**: System category:
   - "ERP" - Enterprise Resource Planning
   - "PMS" - Property Management System
   - "POS" - Point of Sale
   - "CRM" - Customer Relationship Management
   - "CMMS" - Maintenance Management
   - "BI" - Business Intelligence
   - "Productivity" - Office tools (Excel, Word, etc.)
   - "Communication" - Communication tools (Outlook, Teams, WhatsApp)
   - "Other" - Other systems
3. **integration_pain_points**: Specific integration problems (e.g., ["No integra con SAP", "Doble entrada manual", "Datos no sincronizados"])
4. **data_quality_issues**: Data quality problems (e.g., ["Errores de conciliación", "Datos inconsistentes", "Falta validación"])
5. **user_satisfaction_score**: Infer satisfaction from 1-10 based on sentiment:
   - 9-10: "me gusta", "funciona bien", "excelente", "perfecto"
   - 7-8: "útil", "bueno", "fácil de usar"
   - 5-6: Neutral, no strong opinion expressed
   - 3-4: "complicado", "lento", "difícil"
   - 1-2: "no sirve", "no funciona", "malo", "falla mucho"
6. **replacement_candidate**: true if satisfaction <= 3 OR explicit mention of replacement needed
7. **adoption_rate**: Percentage if mentioned (e.g., "solo 30% lo usa" → 0.3)
8. **confidence_score**: 0.0-1.0 based on how explicit the mention is
9. **extraction_reasoning**: Brief explanation

**Important Guidelines:**
- Extract both digital systems AND manual tools (Excel, paper forms)
- Identify integration problems between systems
- Note data quality issues (errors, inconsistencies, lack of validation)
- Infer user satisfaction from language used
- Flag systems as replacement candidates if satisfaction is very low
- Extract adoption rate if mentioned
- Be specific about pain points (not just "tiene problemas")

**Examples of Systems:**
- "SAP es lento y complicado, nadie lo usa" → SAP with satisfaction=3, replacement_candidate=true
- "Opera funciona bien para reservas" → Opera with satisfaction=8
- "Tengo que pasar datos de Simphony a SAP manualmente" → Both systems with integration pain point
- "Excel para todo porque los sistemas no hablan entre sí" → Excel with high usage, integration pain point

**Return Format:**
{{
  "systems": [
    {{
      "name": "System name",
      "domain": "Area of use",
      "vendor": "Vendor name or null",
      "type": "ERP|PMS|POS|CRM|CMMS|BI|Productivity|Communication|Other",
      "integration_pain_points": ["Specific integration issue 1", "Issue 2"],
      "data_quality_issues": ["Specific data quality issue 1", "Issue 2"],
      "user_satisfaction_score": 1-10,
      "replacement_candidate": true|false,
      "adoption_rate": 0.0-1.0 or null,
      "confidence_score": 0.0-1.0,
      "extraction_reasoning": "Brief explanation"
    }}
  ]
}}

If no systems are found, return {{"systems": []}}.
"""
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert in enterprise systems analysis, integration architecture, and user experience. You extract structured information about systems, their integration issues, and user satisfaction. Always return valid JSON."
                },
                {"role": "user", "content": prompt}
            ]
            
            response_content = call_llm_with_fallback(self.client, messages, temperature=0.1)
            
            if not response_content:
                print("Warning: All LLM models failed for system extraction")
                return []
            
            result = json.loads(response_content)
            systems = result.get("systems", [])
            
            # Validate and set defaults
            for system in systems:
                if not system.get("name"):
                    continue
                
                # Set defaults for missing fields
                system.setdefault("domain", "Unknown")
                system.setdefault("vendor", None)
                system.setdefault("type", "Other")
                system.setdefault("integration_pain_points", [])
                system.setdefault("data_quality_issues", [])
                system.setdefault("user_satisfaction_score", 5.0)
                system.setdefault("replacement_candidate", False)
                system.setdefault("adoption_rate", None)
                system.setdefault("confidence_score", 0.8)
                system.setdefault("extraction_reasoning", "Extracted by LLM")
                system["extraction_source"] = "llm_extraction"
            
            return systems
            
        except Exception as e:
            print(f"Warning: LLM extraction failed: {e}")
            return []



class DecisionPointExtractor:
    """Extracts decision points and escalation logic from interview text"""
    
    # Decision-making keywords
    DECISION_KEYWORDS = [
        "decido", "decidir", "decisión", "apruebo", "aprobar", "aprobación",
        "autorizo", "autorizar", "autorización", "evalúo", "evaluar",
        "priorizo", "priorizar", "clasifico", "clasificar"
    ]
    
    # Escalation keywords
    ESCALATION_KEYWORDS = [
        "escalo", "escalar", "escalación", "elevo", "elevar",
        "consulto", "consultar", "requiere aprobación", "necesita aprobación",
        "reporto a", "informo a"
    ]
    
    # Authority limit patterns
    AUTHORITY_PATTERNS = [
        r"hasta\s+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
        r"límite\s+de\s+(?:autorización\s+)?(?:es\s+)?\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
        r"puedo\s+aprobar\s+hasta\s+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
        r"autoridad\s+de\s+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)"
    ]
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract decision points from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of decision point entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text for analysis
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # Rule-based extraction
        rule_based_decisions = self._rule_based_extraction(full_text, meta)
        
        # LLM extraction (if available)
        llm_decisions = self._llm_extraction(full_text, meta)
        
        # Merge results
        all_decisions = self._merge_decisions(rule_based_decisions, llm_decisions)
        
        return all_decisions
    
    def _rule_based_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Extract decision points using pattern matching"""
        decisions = []
        text_lower = text.lower()
        
        # Check if this person makes decisions
        has_decision_authority = any(keyword in text_lower for keyword in self.DECISION_KEYWORDS)
        
        if not has_decision_authority:
            return decisions
        
        # Extract decision type from role and context
        role = meta.get("role", "")
        decision_type = self._infer_decision_type(text, role)
        
        if decision_type:
            decision_data = {
                "decision_type": decision_type,
                "decision_maker_role": role,
                "decision_criteria": self._extract_criteria(text),
                "approval_required": self._check_approval_required(text),
                "approval_threshold": None,
                "authority_limit_usd": self._extract_authority_limit(text),
                "escalation_trigger": self._extract_escalation_trigger(text),
                "escalation_to_role": self._extract_escalation_target(text),
                "related_process": self._infer_related_process(text, role),
                "confidence_score": 0.7,
                "extraction_source": "rule_based",
                "extraction_reasoning": f"Found decision-making language for {role}"
            }
            decisions.append(decision_data)
        
        return decisions
    
    def _infer_decision_type(self, text: str, role: str) -> Optional[str]:
        """Infer what type of decisions this person makes"""
        text_lower = text.lower()
        role_lower = role.lower()
        
        # Role-based decision types
        if "ingenier" in role_lower or "mantenimiento" in role_lower:
            if "prioriz" in text_lower or "clasific" in text_lower:
                return "Priorización de mantenimiento"
            return "Gestión de mantenimiento"
        
        elif "contab" in role_lower or "financ" in role_lower:
            if "aprueb" in text_lower or "autoriz" in text_lower:
                return "Aprobación de pagos"
            return "Gestión financiera"
        
        elif "compras" in role_lower or "adquisic" in role_lower:
            return "Aprobación de compras"
        
        elif "gerente" in role_lower or "director" in role_lower:
            if "presupuesto" in text_lower:
                return "Aprobación de presupuesto"
            return "Decisiones estratégicas"
        
        elif "chef" in role_lower or "cocina" in role_lower:
            return "Gestión de menú y producción"
        
        # Context-based decision types
        if "prioriz" in text_lower:
            return "Priorización de tareas"
        elif "aprueb" in text_lower or "autoriz" in text_lower:
            return "Aprobación de solicitudes"
        elif "evalú" in text_lower:
            return "Evaluación y selección"
        
        return None
    
    def _extract_criteria(self, text: str) -> List[str]:
        """Extract decision criteria from text"""
        criteria = []
        text_lower = text.lower()
        
        # Common criteria patterns
        criteria_patterns = {
            "criticidad": ["criticidad", "crítico", "urgente", "urgencia"],
            "impacto": ["impacto", "afecta", "afectación"],
            "costo": ["costo", "precio", "monto", "presupuesto"],
            "seguridad": ["seguridad", "riesgo", "peligro"],
            "calidad": ["calidad", "estándar", "especificación"],
            "tiempo": ["tiempo", "plazo", "fecha límite"],
            "disponibilidad": ["disponibilidad", "stock", "inventario"]
        }
        
        for criterion, keywords in criteria_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                criteria.append(criterion.capitalize())
        
        return criteria
    
    def _check_approval_required(self, text: str) -> bool:
        """Check if approval is required for decisions"""
        text_lower = text.lower()
        
        approval_phrases = [
            "requiere aprobación",
            "necesita aprobación",
            "debe ser aprobado",
            "solicito aprobación",
            "pido autorización"
        ]
        
        return any(phrase in text_lower for phrase in approval_phrases)
    
    def _extract_authority_limit(self, text: str) -> Optional[float]:
        """Extract monetary authority limit"""
        for pattern in self.AUTHORITY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(",", "")
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_escalation_trigger(self, text: str) -> Optional[str]:
        """Extract what triggers escalation"""
        text_lower = text.lower()
        
        # Look for escalation patterns
        escalation_patterns = [
            r"escalo\s+(?:cuando|si|en caso de)\s+([^.]+)",
            r"elevo\s+(?:cuando|si|en caso de)\s+([^.]+)",
            r"consulto\s+(?:cuando|si|en caso de)\s+([^.]+)",
            r"requiere\s+aprobación\s+(?:cuando|si|en caso de)\s+([^.]+)"
        ]
        
        for pattern in escalation_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1).strip()
        
        # Common escalation triggers
        if "afecta seguridad" in text_lower:
            return "Afecta seguridad"
        elif "supera presupuesto" in text_lower or "excede presupuesto" in text_lower:
            return "Supera presupuesto aprobado"
        elif "impacto alto" in text_lower or "alto impacto" in text_lower:
            return "Alto impacto en operaciones"
        
        return None
    
    def _extract_escalation_target(self, text: str) -> Optional[str]:
        """Extract who to escalate to"""
        text_lower = text.lower()
        
        # Look for escalation target patterns
        target_patterns = [
            r"escalo\s+a(?:l)?\s+([^.,]+)",
            r"elevo\s+a(?:l)?\s+([^.,]+)",
            r"consulto\s+(?:con|a(?:l)?)\s+([^.,]+)",
            r"reporto\s+a(?:l)?\s+([^.,]+)",
            r"informo\s+a(?:l)?\s+([^.,]+)"
        ]
        
        for pattern in target_patterns:
            match = re.search(pattern, text_lower)
            if match:
                target = match.group(1).strip()
                # Clean up and capitalize
                return target.title()
        
        # Common escalation targets by role
        if "gerente general" in text_lower:
            return "Gerente General"
        elif "director" in text_lower:
            return "Director"
        elif "gerente" in text_lower:
            return "Gerente"
        elif "jefe" in text_lower:
            return "Jefe"
        
        return None
    
    def _infer_related_process(self, text: str, role: str) -> Optional[str]:
        """Infer which process this decision relates to"""
        text_lower = text.lower()
        role_lower = role.lower()
        
        # Context-based process inference (check text first for more specific matches)
        if "pago" in text_lower:
            return "Gestión de pagos"
        elif "mantenimiento" in text_lower:
            return "Gestión de mantenimiento"
        elif "compra" in text_lower or "adquisic" in text_lower:
            return "Gestión de compras"
        elif "contrat" in text_lower:
            return "Gestión de contratación"
        
        # Role-based process inference (fallback if no context match)
        if "ingenier" in role_lower or "mantenimiento" in role_lower:
            return "Gestión de mantenimiento"
        elif "contab" in role_lower:
            return "Gestión contable"
        elif "compras" in role_lower:
            return "Gestión de compras"
        elif "chef" in role_lower:
            return "Gestión de cocina"
        
        return None
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Use LLM to extract decision points with deeper understanding"""
        
        if not self.client:
            return []
        
        prompt = f"""You are analyzing an interview to extract decision-making authority and escalation logic. Focus on identifying WHO decides WHAT, WHEN they escalate, and TO WHOM.

**Interview Context:**
- Role: {meta.get('role', 'Unknown')}
- Company: {meta.get('company', 'Unknown')}

**Interview Text:**
{text[:4000]}

**Your Task:**
Extract ALL decision points where this person has decision-making authority or describes decision/escalation processes.

**A decision point exists when:**
1. The person explicitly says they make decisions ("yo decido", "yo apruebo", "yo autorizo")
2. They describe decision criteria ("evalúo basado en...", "priorizo según...")
3. They mention approval authority ("puedo aprobar hasta...", "tengo autoridad de...")
4. They describe escalation logic ("escalo cuando...", "consulto si...", "requiere aprobación de...")
5. They explain prioritization ("clasifico por...", "ordeno según...")

**Look for these patterns:**
- "Yo decido/apruebo/autorizo [what]"
- "Evalúo/priorizo basado en [criteria]"
- "Puedo aprobar hasta [amount]"
- "Escalo/consulto cuando [trigger]"
- "Requiere aprobación de [role]"
- "Mi límite es [amount]"
- "Reporto a [role] si [condition]"

**For each decision point, extract:**

1. **decision_type**: What kind of decision (e.g., "Priorización de mantenimiento", "Aprobación de pagos", "Gestión de inventario")
2. **decision_maker_role**: Who makes the decision (use the role from interview metadata)
3. **decision_criteria**: List of criteria used to decide (e.g., ["Criticidad", "Impacto en huésped", "Costo", "Seguridad"])
4. **approval_required**: true if they need someone else's approval, false if they decide independently
5. **approval_threshold**: Description of when approval is needed (e.g., "Montos mayores a $5000")
6. **authority_limit_usd**: Numeric dollar amount of their authority limit (if mentioned)
7. **escalation_trigger**: What condition triggers escalation (e.g., "Afecta seguridad", "Supera presupuesto", "Alto impacto")
8. **escalation_to_role**: Who they escalate to (e.g., "Gerente General", "Director", "Jefe inmediato")
9. **related_process**: Business process this decision relates to (e.g., "Gestión de mantenimiento", "Proceso de compras")
10. **confidence_score**: 0.0-1.0 based on how explicit the mention is
11. **extraction_reasoning**: Brief explanation of why you extracted this

**Important Guidelines:**
- Focus on ACTUAL decision authority, not just tasks they perform
- Extract specific criteria, not vague statements
- If they mention "yo decido" or "yo apruebo", that's a decision point
- Escalation logic is valuable even if they don't have final authority
- Be specific about escalation triggers (not just "when needed")
- Extract numeric authority limits when mentioned
- One person may have multiple decision points for different types of decisions

**Examples of Decision Points:**
- "Yo priorizo las solicitudes de mantenimiento según criticidad y seguridad" → Decision point about maintenance prioritization
- "Puedo aprobar compras hasta $5000, más de eso requiere aprobación del gerente" → Decision point with authority limit and escalation
- "Escalo al gerente cuando afecta la experiencia del huésped" → Escalation logic
- "Evalúo proveedores basado en precio, calidad y tiempo de entrega" → Decision criteria for vendor selection

**Return Format:**
{{
  "decisions": [
    {{
      "decision_type": "Type of decision",
      "decision_maker_role": "Role from interview",
      "decision_criteria": ["Criterion 1", "Criterion 2"],
      "approval_required": true|false,
      "approval_threshold": "Description or null",
      "authority_limit_usd": number or null,
      "escalation_trigger": "Trigger description or null",
      "escalation_to_role": "Role name or null",
      "related_process": "Process name",
      "confidence_score": 0.0-1.0,
      "extraction_reasoning": "Brief explanation"
    }}
  ]
}}

If no decision points are found, return {{"decisions": []}}.
"""
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert organizational analyst specializing in decision-making authority, approval workflows, and escalation logic. You extract structured information about who decides what and when they escalate. Always return valid JSON."
                },
                {"role": "user", "content": prompt}
            ]
            
            response_content = call_llm_with_fallback(self.client, messages, temperature=0.1)
            
            if not response_content:
                print("Warning: All LLM models failed for decision point extraction")
                return []
            
            result = json.loads(response_content)
            decisions = result.get("decisions", [])
            
            # Add extraction source and validate
            for decision in decisions:
                decision["extraction_source"] = "llm_extraction"
                
                # Ensure required fields exist
                if not decision.get("decision_type") or not decision.get("decision_maker_role"):
                    continue
                
                # Set defaults for missing fields
                decision.setdefault("decision_criteria", [])
                decision.setdefault("approval_required", False)
                decision.setdefault("approval_threshold", None)
                decision.setdefault("authority_limit_usd", None)
                decision.setdefault("escalation_trigger", None)
                decision.setdefault("escalation_to_role", None)
                decision.setdefault("related_process", None)
                decision.setdefault("confidence_score", 0.8)
                decision.setdefault("extraction_reasoning", "Extracted by LLM")
            
            return decisions
            
        except Exception as e:
            print(f"Warning: LLM extraction failed: {e}")
            return []
    
    def _merge_decisions(self, rule_based: List[Dict], llm_based: List[Dict]) -> List[Dict]:
        """Merge and deduplicate decisions from different extraction methods"""
        merged = {}
        
        # Add rule-based decisions
        for decision in rule_based:
            key = decision["decision_type"].lower()
            merged[key] = decision
        
        # Merge LLM decisions (prefer LLM data if confidence is higher)
        for decision in llm_based:
            key = decision["decision_type"].lower()
            if key in merged:
                if decision.get("confidence_score", 0) > merged[key].get("confidence_score", 0):
                    # Merge criteria
                    existing_criteria = set(merged[key].get("decision_criteria", []))
                    new_criteria = set(decision.get("decision_criteria", []))
                    decision["decision_criteria"] = list(existing_criteria | new_criteria)
                    merged[key] = decision
            else:
                merged[key] = decision
        
        return list(merged.values())



class DataFlowExtractor:
    """Extracts data flow entities from interview text"""
    
    # Data movement keywords
    DATA_MOVEMENT_KEYWORDS = [
        "paso datos", "transferir", "exportar", "importar",
        "conciliar", "conciliación", "integrar", "integración",
        "sincronizar", "copiar", "migrar", "cargar"
    ]
    
    # Transfer methods
    TRANSFER_METHODS = {
        "manual": ["manual", "manualmente", "a mano", "copio", "escribo"],
        "api": ["api", "automático", "integración", "conectado"],
        "export_import": ["exporto", "exportar", "importo", "importar", "archivo", "excel", "csv"],
        "database": ["base de datos", "query", "consulta sql"]
    }
    
    # Data quality issue patterns
    DATA_QUALITY_PATTERNS = [
        "error", "inconsistencia", "no coincide", "diferencia",
        "falta", "duplicado", "incorrecto", "desactualizado"
    ]
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract data flows from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of data flow entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text for analysis
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # Rule-based extraction
        rule_based_flows = self._rule_based_extraction(full_text, meta)
        
        # LLM extraction (if available)
        llm_flows = self._llm_extraction(full_text, meta)
        
        # Merge results
        all_flows = self._merge_flows(rule_based_flows, llm_flows)
        
        return all_flows
    
    def _rule_based_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Extract data flows using pattern matching"""
        flows = []
        text_lower = text.lower()
        
        # Check if data movement is mentioned
        has_data_movement = any(keyword in text_lower for keyword in self.DATA_MOVEMENT_KEYWORDS)
        
        if not has_data_movement:
            return flows
        
        # Extract system pairs (source -> target)
        system_pairs = self._extract_system_pairs(text)
        
        for source, target in system_pairs:
            flow_data = {
                "source_system": source,
                "target_system": target,
                "data_type": self._infer_data_type(text, source, target),
                "transfer_method": self._classify_transfer_method(text),
                "transfer_frequency": self._infer_transfer_frequency(text),
                "data_quality_issues": self._extract_data_quality_issues(text),
                "pain_points": self._extract_pain_points(text, source, target),
                "related_process": self._infer_related_process(text, meta.get("role", "")),
                "confidence_score": 0.7,
                "extraction_source": "rule_based",
                "extraction_reasoning": f"Found data movement from {source} to {target}"
            }
            flows.append(flow_data)
        
        return flows
    
    def _extract_system_pairs(self, text: str) -> List[Tuple[str, str]]:
        """Extract source-target system pairs from text"""
        pairs = []
        text_lower = text.lower()
        
        # Pattern 1: "de X a Y" (flexible - allows words between)
        pattern1 = r"de\s+(?:\w+\s+)?([A-Za-z0-9]+)\s+a\s+([A-Za-z0-9]+)"
        matches = re.findall(pattern1, text, re.IGNORECASE)
        for source, target in matches:
            source = source.strip().title()
            target = target.strip().title()
            if self._is_likely_system(source) and self._is_likely_system(target):
                pairs.append((source, target))
        
        # Pattern 2: "desde X hacia Y"
        pattern2 = r"desde\s+(?:\w+\s+)?([A-Za-z0-9]+)\s+(?:hacia|a)\s+([A-Za-z0-9]+)"
        matches = re.findall(pattern2, text, re.IGNORECASE)
        for source, target in matches:
            source = source.strip().title()
            target = target.strip().title()
            if self._is_likely_system(source) and self._is_likely_system(target):
                pairs.append((source, target))
        
        # Pattern 3: "exporto [data type] de X e importo a Y"
        # More flexible - allows "ventas de", "datos de", etc.
        pattern3 = r"(?:exporto|exportar)(?:\s+\w+)?\s+de\s+([A-Za-z0-9]+)\s+(?:e|y)\s+(?:importo|importar)\s+a\s+([A-Za-z0-9]+)"
        matches = re.findall(pattern3, text, re.IGNORECASE)
        for source, target in matches:
            source = source.strip().title()
            target = target.strip().title()
            if self._is_likely_system(source) and self._is_likely_system(target):
                pairs.append((source, target))
        
        # Pattern 4: "paso [data type] de X a Y"
        pattern4 = r"(?:paso|pasar|transferir)(?:\s+\w+)?\s+de\s+([A-Za-z0-9]+)\s+a\s+([A-Za-z0-9]+)"
        matches = re.findall(pattern4, text, re.IGNORECASE)
        for source, target in matches:
            source = source.strip().title()
            target = target.strip().title()
            if self._is_likely_system(source) and self._is_likely_system(target):
                pairs.append((source, target))
        
        # Pattern 5: "entre X y Y" (bidirectional)
        pattern5 = r"entre\s+([A-Za-z0-9]+)\s+y\s+([A-Za-z0-9]+)"
        matches = re.findall(pattern5, text, re.IGNORECASE)
        for sys1, sys2 in matches:
            sys1 = sys1.strip().title()
            sys2 = sys2.strip().title()
            if self._is_likely_system(sys1) and self._is_likely_system(sys2):
                # Add both directions for bidirectional flow
                pairs.append((sys1, sys2))
                pairs.append((sys2, sys1))
        
        # Pattern 6: "concilio X con Y"
        pattern6 = r"concilio\s+([A-Za-z0-9]+)\s+con\s+([A-Za-z0-9]+)"
        matches = re.findall(pattern6, text, re.IGNORECASE)
        for sys1, sys2 in matches:
            sys1 = sys1.strip().title()
            sys2 = sys2.strip().title()
            if self._is_likely_system(sys1) and self._is_likely_system(sys2):
                pairs.append((sys1, sys2))
        
        return list(set(pairs))  # Remove duplicates
    
    def _is_likely_system(self, name: str) -> bool:
        """Check if a name is likely a system name"""
        name_lower = name.lower().strip()
        
        # Avoid common non-system words first
        non_systems = [
            "el", "la", "los", "las", "un", "una", "este", "esta",
            "ese", "esa", "aquel", "aquella", "mi", "tu", "su",
            "datos", "información", "archivo", "documento", "de", "a",
            "y", "e", "o", "u", "con", "sin", "para", "por"
        ]
        
        if name_lower in non_systems:
            return False
        
        # Too short or too long
        if len(name_lower) < 2 or len(name_lower) > 30:
            return False
        
        # Common system names
        known_systems = [
            "sap", "opera", "simphony", "excel", "outlook", "teams",
            "whatsapp", "jira", "trello", "pos", "erp", "crm",
            "sistema", "plataforma", "software", "micros", "satcom"
        ]
        
        if any(sys in name_lower for sys in known_systems):
            return True
        
        # Has typical system name patterns (CamelCase, acronyms, etc.)
        if re.match(r'^[A-Z]{2,}$', name.strip()):  # Acronym like SAP, ERP
            return True
        
        if re.match(r'^[A-Z][a-z]+(?:[A-Z][a-z]+)+$', name.strip()):  # CamelCase
            return True
        
        return False
    
    def _infer_data_type(self, text: str, source: str, target: str) -> str:
        """Infer what type of data is being transferred"""
        text_lower = text.lower()
        
        # Look for data type mentions near the system names
        data_types = {
            "ventas": ["venta", "ventas", "factura", "ticket"],
            "inventario": ["inventario", "stock", "existencia", "producto"],
            "financiero": ["pago", "cobro", "factura", "contable", "financiero"],
            "cliente": ["cliente", "huésped", "reserva", "contacto"],
            "empleado": ["empleado", "personal", "nómina", "rrhh"],
            "producción": ["producción", "manufactura", "orden de trabajo"],
            "compras": ["compra", "orden de compra", "proveedor", "adquisición"]
        }
        
        for data_type, keywords in data_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return data_type.capitalize()
        
        return "Datos operacionales"
    
    def _classify_transfer_method(self, text: str) -> str:
        """Classify how data is transferred"""
        text_lower = text.lower()
        
        # Check for export/import first (more specific)
        if any(keyword in text_lower for keyword in self.TRANSFER_METHODS["export_import"]):
            return "Export/Import"
        
        # Check for API
        if any(keyword in text_lower for keyword in self.TRANSFER_METHODS["api"]):
            return "API"
        
        # Check for database
        if any(keyword in text_lower for keyword in self.TRANSFER_METHODS["database"]):
            return "Database Query"
        
        # Check for manual
        if any(keyword in text_lower for keyword in self.TRANSFER_METHODS["manual"]):
            return "Manual"
        
        # Default to manual if data movement is mentioned but method is unclear
        return "Manual"
    
    def _infer_transfer_frequency(self, text: str) -> str:
        """Infer how often data is transferred"""
        text_lower = text.lower()
        
        frequency_patterns = {
            "Hourly": ["cada hora", "por hora", "horario"],
            "Daily": ["diario", "cada día", "todos los días", "diariamente"],
            "Weekly": ["semanal", "cada semana", "semanalmente"],
            "Monthly": ["mensual", "cada mes", "mensualmente", "cierre mensual"],
            "Real-time": ["tiempo real", "inmediato", "continuo", "automático"],
            "On-demand": ["cuando se necesita", "bajo demanda", "ocasional"]
        }
        
        for frequency, keywords in frequency_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return frequency
        
        return "Daily"  # Default assumption
    
    def _extract_data_quality_issues(self, text: str) -> List[str]:
        """Extract data quality issues mentioned"""
        issues = []
        text_lower = text.lower()
        
        issue_patterns = {
            "Errores de conciliación": ["conciliación", "concilia"],
            "Datos inconsistentes": ["inconsistente", "no coincide", "discrepancia"],
            "Datos faltantes": ["falta", "incompleto", "no está"],
            "Datos duplicados": ["duplicado", "repetido"],
            "Datos incorrectos": ["incorrecto", "erróneo", "mal"],
            "Datos desactualizados": ["desactualizado", "viejo", "antiguo"],
            "Falta de validación": ["sin validar", "no se valida", "no hay control"]
        }
        
        for issue, keywords in issue_patterns.items():
            # Check if ANY keyword is present
            if any(keyword in text_lower for keyword in keywords):
                issues.append(issue)
        
        return issues
    
    def _extract_pain_points(self, text: str, source: str, target: str) -> List[str]:
        """Extract pain points related to this data flow"""
        pain_points = []
        text_lower = text.lower()
        
        pain_patterns = {
            "Doble entrada manual": ["doble entrada", "entrar dos veces", "duplicar entrada"],
            "Propenso a errores": ["propenso a error", "equivocación", "falla"],
            "Consume mucho tiempo": ["toma tiempo", "toma mucho tiempo", "demora", "lento", "horas"],
            "Falta de trazabilidad": ["no hay trazabilidad", "no se puede rastrear"],
            "Pérdida de información": ["se pierde", "pérdida de información"],
            "Requiere conciliación manual": ["conciliar manualmente", "revisar manualmente"]
        }
        
        for pain, keywords in pain_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                pain_points.append(pain)
        
        return pain_points
    
    def _infer_related_process(self, text: str, role: str) -> Optional[str]:
        """Infer which process this data flow relates to"""
        text_lower = text.lower()
        role_lower = role.lower()
        
        # Process patterns
        if "cierre" in text_lower:
            if "diario" in text_lower:
                return "Cierre diario"
            elif "mensual" in text_lower:
                return "Cierre mensual"
            return "Proceso de cierre"
        
        if "venta" in text_lower or "factura" in text_lower:
            return "Gestión de ventas"
        
        if "inventario" in text_lower or "stock" in text_lower:
            return "Gestión de inventario"
        
        if "pago" in text_lower or "cobro" in text_lower:
            return "Gestión de pagos"
        
        if "compra" in text_lower:
            return "Gestión de compras"
        
        if "reserva" in text_lower:
            return "Gestión de reservas"
        
        # Role-based inference
        if "contab" in role_lower:
            return "Proceso contable"
        elif "finanz" in role_lower:
            return "Proceso financiero"
        elif "almacén" in role_lower or "inventario" in role_lower:
            return "Gestión de inventario"
        
        return None
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Use LLM to extract data flows with deeper understanding"""
        
        if not self.client:
            return []
        
        prompt = f"""You are analyzing an interview to extract data flows between systems. Focus on identifying WHERE data moves, HOW it moves, and WHAT problems exist.

**Interview Context:**
- Role: {meta.get('role', 'Unknown')}
- Company: {meta.get('company', 'Unknown')}

**Interview Text:**
{text[:4000]}

**Your Task:**
Extract ALL data flows between systems. A data flow exists when:
1. Data is transferred from one system to another
2. Systems are reconciled or synchronized
3. Data is exported from one system and imported to another
4. Manual data entry happens between systems

**Look for these patterns:**
- "paso datos de X a Y" / "transferir de X a Y"
- "exporto de X e importo a Y"
- "concilio X con Y" / "reconciliar entre X y Y"
- "doble entrada" (manual entry in multiple systems)
- "integración entre X y Y"
- Manual processes that move data

**For each data flow, extract:**

1. **source_system**: The system where data originates (e.g., "Simphony", "Opera", "SAP")
2. **target_system**: The system where data goes (e.g., "SAP", "Excel", "Opera")
3. **data_type**: What kind of data (e.g., "Ventas", "Inventario", "Pagos", "Reservas")
4. **transfer_method**: How data moves:
   - "Manual" - typed by hand, copy-paste
   - "Export/Import" - export file from one, import to another
   - "API" - automatic integration
   - "Database Query" - direct database access
5. **transfer_frequency**: How often (Hourly, Daily, Weekly, Monthly, Real-time, On-demand)
6. **data_quality_issues**: Problems with data accuracy, completeness, consistency
7. **pain_points**: Specific problems mentioned (time consuming, error-prone, etc.)
8. **related_process**: Business process this supports (e.g., "Cierre diario", "Gestión de inventario")
9. **confidence_score**: 0.0-1.0 based on how explicit the mention is
10. **extraction_reasoning**: Brief explanation of why you extracted this flow

**Important:**
- System names should be proper nouns (SAP, Opera, Simphony, Excel, etc.)
- Don't confuse data types with system names ("ventas" is data, "Simphony" is system)
- If someone mentions "doble entrada" or "entrar en dos sistemas", that's a data flow
- Reconciliation ("concilio X con Y") implies bidirectional data flow
- Be specific about pain points (don't just say "problems", say "takes 2 hours daily")

**Return Format:**
{{
  "data_flows": [
    {{
      "source_system": "System name",
      "target_system": "System name",
      "data_type": "Type of data",
      "transfer_method": "Manual|Export/Import|API|Database Query",
      "transfer_frequency": "Hourly|Daily|Weekly|Monthly|Real-time|On-demand",
      "data_quality_issues": ["Specific issue 1", "Specific issue 2"],
      "pain_points": ["Specific pain 1", "Specific pain 2"],
      "related_process": "Process name",
      "confidence_score": 0.0-1.0,
      "extraction_reasoning": "Brief explanation"
    }}
  ]
}}

If no data flows are found, return {{"data_flows": []}}.
"""
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert business analyst specializing in data integration and system architecture. You extract structured information about data flows from interview transcripts with high accuracy. Always return valid JSON."
                },
                {"role": "user", "content": prompt}
            ]
            
            response_content = call_llm_with_fallback(self.client, messages, temperature=0.1)
            
            if not response_content:
                print("Warning: All LLM models failed for data flow extraction")
                return []
            
            result = json.loads(response_content)
            flows = result.get("data_flows", [])
            
            # Add extraction source and validate
            for flow in flows:
                flow["extraction_source"] = "llm_extraction"
                
                # Ensure required fields exist
                if not flow.get("source_system") or not flow.get("target_system"):
                    continue
                
                # Set defaults for missing fields
                flow.setdefault("data_type", "Datos operacionales")
                flow.setdefault("transfer_method", "Manual")
                flow.setdefault("transfer_frequency", "Daily")
                flow.setdefault("data_quality_issues", [])
                flow.setdefault("pain_points", [])
                flow.setdefault("related_process", None)
                flow.setdefault("confidence_score", 0.8)
                flow.setdefault("extraction_reasoning", "Extracted by LLM")
            
            return flows
            
        except Exception as e:
            print(f"Warning: LLM extraction failed: {e}")
            return []
    
    def _merge_flows(self, rule_based: List[Dict], llm_based: List[Dict]) -> List[Dict]:
        """Merge and deduplicate flows from different extraction methods"""
        merged = {}
        
        # Add rule-based flows
        for flow in rule_based:
            key = f"{flow['source_system'].lower()}_{flow['target_system'].lower()}"
            merged[key] = flow
        
        # Merge LLM flows (prefer LLM data if confidence is higher)
        for flow in llm_based:
            key = f"{flow['source_system'].lower()}_{flow['target_system'].lower()}"
            if key in merged:
                if flow.get("confidence_score", 0) > merged[key].get("confidence_score", 0):
                    # Merge data quality issues and pain points
                    existing_issues = set(merged[key].get("data_quality_issues", []))
                    new_issues = set(flow.get("data_quality_issues", []))
                    flow["data_quality_issues"] = list(existing_issues | new_issues)
                    
                    existing_pains = set(merged[key].get("pain_points", []))
                    new_pains = set(flow.get("pain_points", []))
                    flow["pain_points"] = list(existing_pains | new_pains)
                    
                    merged[key] = flow
            else:
                merged[key] = flow
        
        return list(merged.values())



class TemporalPatternExtractor:
    """Extracts temporal pattern entities from interview text"""
    
    # Frequency keywords
    FREQUENCY_KEYWORDS = {
        "Hourly": ["cada hora", "por hora", "horario", "hourly"],
        "Daily": ["diario", "diaria", "cada día", "todos los días", "diariamente", "daily"],
        "Weekly": ["semanal", "cada semana", "semanalmente", "weekly", "cada lunes", "cada martes"],
        "Monthly": ["mensual", "cada mes", "mensualmente", "monthly", "cierre mensual"],
        "Quarterly": ["trimestral", "cada trimestre", "quarterly"],
        "Annually": ["anual", "cada año", "anualmente", "annually"]
    }
    
    # Time patterns
    TIME_PATTERNS = [
        r"(\d{1,2}):(\d{2})\s*(?:am|pm|AM|PM)?",  # 9:00, 14:30
        r"(\d{1,2})\s*(?:am|pm|AM|PM)",  # 9am, 2pm
        r"a las (\d{1,2})",  # a las 9
    ]
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract temporal patterns from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of temporal pattern entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text for analysis
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # Rule-based extraction
        rule_based_patterns = self._rule_based_extraction(full_text, meta)
        
        # LLM extraction (if available)
        llm_patterns = self._llm_extraction(full_text, meta)
        
        # Merge results
        all_patterns = self._merge_patterns(rule_based_patterns, llm_patterns)
        
        return all_patterns
    
    def _rule_based_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Extract temporal patterns using pattern matching"""
        patterns = []
        text_lower = text.lower()
        
        # Check if temporal language is mentioned
        has_temporal = any(
            keyword in text_lower 
            for freq_list in self.FREQUENCY_KEYWORDS.values() 
            for keyword in freq_list
        )
        
        if not has_temporal:
            return patterns
        
        # Extract activities with temporal markers
        temporal_activities = self._extract_temporal_activities(text)
        
        for activity in temporal_activities:
            pattern_data = {
                "activity_name": activity["name"],
                "frequency": activity["frequency"],
                "time_of_day": activity.get("time"),
                "duration_minutes": activity.get("duration"),
                "participants": [meta.get("role", "Unknown")],
                "triggers_actions": [],
                "related_process": self._infer_related_process(text, meta.get("role", "")),
                "confidence_score": 0.7,
                "extraction_source": "rule_based",
                "extraction_reasoning": f"Found temporal pattern: {activity['name']}"
            }
            patterns.append(pattern_data)
        
        return patterns
    
    def _extract_temporal_activities(self, text: str) -> List[Dict]:
        """Extract activities with temporal markers"""
        activities = []
        text_lower = text.lower()
        
        # Look for frequency + activity patterns
        for frequency, keywords in self.FREQUENCY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Try to extract the activity name
                    # Pattern: "frequency + activity" or "activity + frequency"
                    pattern = rf"{keyword}\s+(?:de\s+)?(\w+(?:\s+\w+){{0,3}})"
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    
                    for match in matches:
                        activity_name = match.strip()
                        if len(activity_name) > 3:  # Filter out too short matches
                            # Extract time if mentioned nearby
                            time = self._extract_time_near_activity(text, activity_name)
                            
                            activities.append({
                                "name": activity_name.title(),
                                "frequency": frequency,
                                "time": time,
                                "duration": None
                            })
        
        return activities
    
    def _extract_time_near_activity(self, text: str, activity: str) -> Optional[str]:
        """Extract time mentioned near an activity"""
        # Look for time patterns near the activity mention
        activity_pos = text.lower().find(activity.lower())
        if activity_pos == -1:
            return None
        
        # Check text around the activity (±100 characters)
        context = text[max(0, activity_pos-100):min(len(text), activity_pos+100)]
        
        for pattern in self.TIME_PATTERNS:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return self._normalize_time(match.group(0))
        
        return None
    
    def _normalize_time(self, time_str: str) -> str:
        """Normalize time to 24-hour format"""
        time_str = time_str.lower().strip()
        
        # Handle "a las X" format
        if "a las" in time_str:
            time_str = time_str.replace("a las", "").strip()
        
        # Handle AM/PM
        is_pm = "pm" in time_str
        is_am = "am" in time_str
        time_str = time_str.replace("am", "").replace("pm", "").strip()
        
        # Extract hour and minute
        if ":" in time_str:
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        else:
            hour = int(time_str)
            minute = 0
        
        # Convert to 24-hour format
        if is_pm and hour < 12:
            hour += 12
        elif is_am and hour == 12:
            hour = 0
        
        return f"{hour:02d}:{minute:02d}"
    
    def _infer_related_process(self, text: str, role: str) -> Optional[str]:
        """Infer which process this temporal pattern relates to"""
        text_lower = text.lower()
        role_lower = role.lower()
        
        # Process patterns
        if "reunión" in text_lower or "junta" in text_lower:
            return "Coordinación y reuniones"
        
        if "cierre" in text_lower:
            if "diario" in text_lower:
                return "Cierre diario"
            elif "mensual" in text_lower:
                return "Cierre mensual"
            return "Proceso de cierre"
        
        if "reporte" in text_lower or "informe" in text_lower:
            return "Generación de reportes"
        
        if "inventario" in text_lower:
            return "Gestión de inventario"
        
        if "mantenimiento" in text_lower:
            return "Gestión de mantenimiento"
        
        # Role-based inference
        if "contab" in role_lower:
            return "Proceso contable"
        elif "ingenier" in role_lower:
            return "Gestión de mantenimiento"
        
        return None
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Use LLM to extract temporal patterns with deeper understanding"""
        
        if not self.client:
            return []
        
        prompt = f"""You are analyzing an interview to extract temporal patterns - recurring activities that happen at specific times or frequencies. Focus on identifying WHEN things happen, HOW OFTEN, and HOW LONG they take.

**Interview Context:**
- Role: {meta.get('role', 'Unknown')}
- Company: {meta.get('company', 'Unknown')}

**Interview Text:**
{text[:4000]}

**Your Task:**
Extract ALL temporal patterns - recurring activities with time-based characteristics.

**A temporal pattern exists when:**
1. An activity happens at a specific time ("a las 9am", "por la mañana")
2. An activity happens with a specific frequency ("diario", "cada semana", "mensual")
3. A meeting or coordination happens regularly ("reuniones semanales", "junta mensual")
4. A process has a time-based trigger ("cierre diario", "reporte mensual")
5. Duration is mentioned ("reunión de 30 minutos", "toma 2 horas")

**Look for these patterns:**
- "Diario/cada día a las [time]"
- "Reuniones [frequency]"
- "Cierre [frequency]"
- "Reporte [frequency]"
- "[Activity] cada [frequency]"
- "Todos los [day] a las [time]"
- "[Activity] de [duration] minutos/horas"

**For each temporal pattern, extract:**

1. **activity_name**: Name of the activity (e.g., "Reunión de coordinación", "Cierre diario de ventas", "Revisión de inventario")
2. **frequency**: How often it happens:
   - "Hourly" - every hour
   - "Daily" - every day
   - "Weekly" - every week
   - "Monthly" - every month
   - "Quarterly" - every quarter
   - "Annually" - every year
3. **time_of_day**: Specific time in 24-hour format (e.g., "09:00", "14:30") or null if not mentioned
4. **duration_minutes**: How long it takes in minutes (e.g., 30, 60, 120) or null if not mentioned
5. **participants**: Who participates (roles/departments, e.g., ["Gerente", "Jefes de área", "Equipo de ventas"])
6. **triggers_actions**: What actions this triggers (e.g., ["Asignación de tareas", "Generación de reportes"])
7. **related_process**: Business process this relates to (e.g., "Gestión de mantenimiento", "Proceso de cierre")
8. **confidence_score**: 0.0-1.0 based on how explicit the mention is
9. **extraction_reasoning**: Brief explanation of why you extracted this

**Important Guidelines:**
- Extract SPECIFIC activities, not vague mentions of time
- Include meetings, closings, reports, reviews, and any recurring activity
- Normalize frequency to standard values (Hourly, Daily, Weekly, Monthly, Quarterly, Annually)
- Convert times to 24-hour format (9am → "09:00", 2pm → "14:00")
- Extract duration in minutes (30 minutos → 30, 2 horas → 120)
- Be specific about participants (roles, not just "equipo")
- Identify what actions are triggered by this temporal pattern

**Examples of Temporal Patterns:**
- "Reunión diaria a las 9am con el equipo" → Daily at 09:00
- "Cierre mensual el último día del mes" → Monthly
- "Revisión de inventario cada semana, toma 2 horas" → Weekly, 120 minutes
- "Reporte semanal todos los lunes" → Weekly
- "Junta de coordinación cada viernes a las 3pm, dura 30 minutos" → Weekly at 15:00, 30 minutes

**Return Format:**
{{
  "temporal_patterns": [
    {{
      "activity_name": "Activity name",
      "frequency": "Hourly|Daily|Weekly|Monthly|Quarterly|Annually",
      "time_of_day": "HH:MM" or null,
      "duration_minutes": number or null,
      "participants": ["Role 1", "Role 2"],
      "triggers_actions": ["Action 1", "Action 2"],
      "related_process": "Process name",
      "confidence_score": 0.0-1.0,
      "extraction_reasoning": "Brief explanation"
    }}
  ]
}}

If no temporal patterns are found, return {{"temporal_patterns": []}}.
"""
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert in workflow analysis and time management. You extract structured information about when activities happen, how often, and how long they take. Always return valid JSON."
                },
                {"role": "user", "content": prompt}
            ]
            
            response_content = call_llm_with_fallback(self.client, messages, temperature=0.1)
            
            if not response_content:
                print("Warning: All LLM models failed for temporal pattern extraction")
                return []
            
            result = json.loads(response_content)
            patterns = result.get("temporal_patterns", [])
            
            # Add extraction source and validate
            for pattern in patterns:
                pattern["extraction_source"] = "llm_extraction"
                
                # Ensure required fields exist
                if not pattern.get("activity_name") or not pattern.get("frequency"):
                    continue
                
                # Set defaults for missing fields
                pattern.setdefault("time_of_day", None)
                pattern.setdefault("duration_minutes", None)
                pattern.setdefault("participants", [])
                pattern.setdefault("triggers_actions", [])
                pattern.setdefault("related_process", None)
                pattern.setdefault("confidence_score", 0.8)
                pattern.setdefault("extraction_reasoning", "Extracted by LLM")
            
            return patterns
            
        except Exception as e:
            print(f"Warning: LLM extraction failed: {e}")
            return []
    
    def _merge_patterns(self, rule_based: List[Dict], llm_based: List[Dict]) -> List[Dict]:
        """Merge and deduplicate patterns from different extraction methods"""
        merged = {}
        
        # Add rule-based patterns
        for pattern in rule_based:
            key = f"{pattern['activity_name'].lower()}_{pattern['frequency'].lower()}"
            merged[key] = pattern
        
        # Merge LLM patterns (prefer LLM data if confidence is higher)
        for pattern in llm_based:
            key = f"{pattern['activity_name'].lower()}_{pattern['frequency'].lower()}"
            if key in merged:
                if pattern.get("confidence_score", 0) > merged[key].get("confidence_score", 0):
                    # Merge participants and actions
                    existing_participants = set(merged[key].get("participants", []))
                    new_participants = set(pattern.get("participants", []))
                    pattern["participants"] = list(existing_participants | new_participants)
                    
                    existing_actions = set(merged[key].get("triggers_actions", []))
                    new_actions = set(pattern.get("triggers_actions", []))
                    pattern["triggers_actions"] = list(existing_actions | new_actions)
                    
                    merged[key] = pattern
            else:
                merged[key] = pattern
        
        return list(merged.values())



class FailureModeExtractor:
    """Extracts failure mode entities from interview text"""
    
    # Failure keywords
    FAILURE_KEYWORDS = [
        "falla", "fallo", "se cae", "no funciona", "problema", "error",
        "defecto", "avería", "daño", "roto", "descompuesto",
        "no sirve", "mal estado", "fuera de servicio"
    ]
    
    # Frequency patterns
    FREQUENCY_PATTERNS = {
        "Daily": ["diario", "cada día", "todos los días"],
        "Weekly": ["semanal", "cada semana", "semanalmente"],
        "Monthly": ["mensual", "cada mes", "mensualmente"],
        "Occasionally": ["ocasional", "a veces", "de vez en cuando"],
        "Rarely": ["rara vez", "pocas veces", "casi nunca"]
    }
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract failure modes from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of failure mode entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text for analysis
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # Rule-based extraction
        rule_based_failures = self._rule_based_extraction(full_text, meta)
        
        # LLM extraction (if available)
        llm_failures = self._llm_extraction(full_text, meta)
        
        # Merge results
        all_failures = self._merge_failures(rule_based_failures, llm_failures)
        
        return all_failures
    
    def _rule_based_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Extract failure modes using pattern matching"""
        failures = []
        text_lower = text.lower()
        
        # Check if failure language is mentioned
        has_failure = any(keyword in text_lower for keyword in self.FAILURE_KEYWORDS)
        
        if not has_failure:
            return failures
        
        # Extract failure descriptions
        failure_descriptions = self._extract_failure_descriptions(text)
        
        for description in failure_descriptions:
            failure_data = {
                "failure_description": description,
                "frequency": self._infer_frequency(text),
                "impact_description": self._extract_impact(text),
                "root_cause": None,
                "current_workaround": self._extract_workaround(text),
                "recovery_time_minutes": self._extract_recovery_time(text),
                "proposed_prevention": None,
                "related_process": self._infer_related_process(text, meta.get("role", "")),
                "confidence_score": 0.7,
                "extraction_source": "rule_based",
                "extraction_reasoning": f"Found failure language: {description[:50]}"
            }
            failures.append(failure_data)
        
        return failures
    
    def _extract_failure_descriptions(self, text: str) -> List[str]:
        """Extract failure descriptions from text"""
        descriptions = []
        text_lower = text.lower()
        
        # Look for failure patterns
        for keyword in self.FAILURE_KEYWORDS:
            if keyword in text_lower:
                # Try to extract context around the failure keyword
                pattern = rf"([^.]*{keyword}[^.]*\.)"
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match) > 10:  # Filter out too short matches
                        descriptions.append(match.strip())
        
        return list(set(descriptions))[:3]  # Limit to 3 most relevant
    
    def _infer_frequency(self, text: str) -> str:
        """Infer how often failures occur"""
        text_lower = text.lower()
        
        for frequency, keywords in self.FREQUENCY_PATTERNS.items():
            if any(keyword in text_lower for keyword in keywords):
                return frequency
        
        # Check for frequency indicators
        if any(word in text_lower for word in ["frecuente", "seguido", "constantemente"]):
            return "Weekly"
        elif any(word in text_lower for word in ["rara vez", "pocas veces"]):
            return "Rarely"
        
        return "Occasionally"
    
    def _extract_impact(self, text: str) -> str:
        """Extract impact description"""
        text_lower = text.lower()
        
        impact_keywords = {
            "retraso": "Retraso en operaciones",
            "pérdida": "Pérdida de productividad",
            "queja": "Quejas de clientes",
            "costo": "Incremento de costos",
            "tiempo": "Pérdida de tiempo",
            "parada": "Parada de operaciones"
        }
        
        for keyword, impact in impact_keywords.items():
            if keyword in text_lower:
                return impact
        
        return "Impacto en operaciones"
    
    def _extract_workaround(self, text: str) -> Optional[str]:
        """Extract current workaround"""
        text_lower = text.lower()
        
        workaround_patterns = [
            r"(?:solución temporal|workaround|mientras tanto|por ahora)[:\s]+([^.]+)",
            r"(?:hacemos|hago|usamos)[:\s]+([^.]+)(?:mientras|hasta)",
            r"(?:alternativa|opción)[:\s]+([^.]+)"
        ]
        
        for pattern in workaround_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1).strip().capitalize()
        
        return None
    
    def _extract_recovery_time(self, text: str) -> Optional[int]:
        """Extract recovery time in minutes"""
        text_lower = text.lower()
        
        # Look for time patterns
        time_patterns = [
            (r"(\d+)\s*horas?", 60),  # hours to minutes
            (r"(\d+)\s*minutos?", 1),  # minutes
            (r"(\d+)\s*días?", 1440),  # days to minutes
        ]
        
        for pattern, multiplier in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return int(match.group(1)) * multiplier
        
        return None
    
    def _infer_related_process(self, text: str, role: str) -> Optional[str]:
        """Infer which process this failure relates to"""
        text_lower = text.lower()
        role_lower = role.lower()
        
        # Process patterns
        if "mantenimiento" in text_lower:
            return "Gestión de mantenimiento"
        elif "sistema" in text_lower or "software" in text_lower:
            return "Sistemas de información"
        elif "inventario" in text_lower:
            return "Gestión de inventario"
        elif "producción" in text_lower:
            return "Proceso de producción"
        
        # Role-based inference
        if "ingenier" in role_lower:
            return "Gestión de mantenimiento"
        elif "ti" in role_lower or "sistemas" in role_lower:
            return "Sistemas de información"
        
        return None
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Use LLM to extract failure modes with deeper understanding"""
        
        if not self.client:
            return []
        
        prompt = f"""You are analyzing an interview to extract failure modes - things that go wrong, break, or don't work properly. Focus on identifying WHAT fails, HOW OFTEN, WHAT the impact is, and HOW people work around it.

**Interview Context:**
- Role: {meta.get('role', 'Unknown')}
- Company: {meta.get('company', 'Unknown')}

**Interview Text:**
{text[:4000]}

**Your Task:**
Extract ALL failure modes - problems, breakdowns, errors, or things that don't work properly.

**A failure mode exists when:**
1. Something breaks or stops working ("se cae", "falla", "no funciona")
2. A system or equipment has problems ("problemas con", "errores en")
3. A recurring issue is mentioned ("siempre pasa", "problema recurrente")
4. Workarounds or manual fixes are described
5. Downtime or recovery time is mentioned

**Look for these patterns:**
- "Se cae [system/equipment]"
- "Falla [what]"
- "No funciona [what]"
- "Problema con [what]"
- "Siempre/frecuentemente [problem]"
- "Tarda [time] en resolverse"
- "Mientras tanto hacemos [workaround]"
- "La solución temporal es [workaround]"

**For each failure mode, extract:**

1. **failure_description**: Clear description of what fails (e.g., "Sistema de inventario se cae", "Falta de repuestos críticos", "Errores en conciliación")
2. **frequency**: How often it happens:
   - "Daily" - every day
   - "Weekly" - every week
   - "Monthly" - every month
   - "Occasionally" - sometimes
   - "Rarely" - rarely
3. **impact_description**: What happens when it fails (e.g., "Retraso de 2-3 días en reparaciones", "Quejas de huéspedes", "Pérdida de ventas")
4. **root_cause**: Why it happens (e.g., "Inventario no automatizado", "Sistemas no integrados", "Falta de mantenimiento preventivo")
5. **current_workaround**: How they work around it now (e.g., "Compra de emergencia a proveedores locales", "Entrada manual en Excel", "Llamar por teléfono")
6. **recovery_time_minutes**: How long to fix/recover (in minutes: 30, 120, 2880 for 2 days, etc.)
7. **proposed_prevention**: How to prevent it (e.g., "Sistema de inventario con alertas automáticas", "Integración entre sistemas")
8. **related_process**: Business process affected (e.g., "Gestión de mantenimiento", "Proceso de ventas")
9. **confidence_score**: 0.0-1.0 based on how explicit the mention is
10. **extraction_reasoning**: Brief explanation of why you extracted this

**Important Guidelines:**
- Focus on ACTUAL failures, not potential risks
- Extract specific failure descriptions, not vague "problems"
- Identify root causes when mentioned or clearly implied
- Capture workarounds even if they're not ideal solutions
- Convert recovery time to minutes (2 horas → 120, 3 días → 4320)
- Link to automation candidates when prevention is mentioned
- Be specific about impact (not just "bad", but "retraso de 2 días")

**Examples of Failure Modes:**
- "El sistema se cae cada semana, tarda 2 horas en volver" → Weekly failure, 120 min recovery
- "Falta de repuestos críticos, compramos de emergencia (más caro)" → Workaround identified
- "Errores de conciliación por sistemas no integrados, hacemos manual en Excel" → Root cause + workaround
- "Equipos se dañan por falta de mantenimiento preventivo" → Root cause identified

**Return Format:**
{{
  "failure_modes": [
    {{
      "failure_description": "Clear description",
      "frequency": "Daily|Weekly|Monthly|Occasionally|Rarely",
      "impact_description": "Specific impact",
      "root_cause": "Why it happens or null",
      "current_workaround": "How they work around it or null",
      "recovery_time_minutes": number or null,
      "proposed_prevention": "How to prevent or null",
      "related_process": "Process name",
      "confidence_score": 0.0-1.0,
      "extraction_reasoning": "Brief explanation"
    }}
  ]
}}

If no failure modes are found, return {{"failure_modes": []}}.
"""
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert in reliability engineering and failure analysis. You extract structured information about what goes wrong, why it happens, and how people work around problems. Always return valid JSON."
                },
                {"role": "user", "content": prompt}
            ]
            
            response_content = call_llm_with_fallback(self.client, messages, temperature=0.1)
            
            if not response_content:
                print("Warning: All LLM models failed for failure mode extraction")
                return []
            
            result = json.loads(response_content)
            failures = result.get("failure_modes", [])
            
            # Add extraction source and validate
            for failure in failures:
                failure["extraction_source"] = "llm_extraction"
                
                # Ensure required fields exist
                if not failure.get("failure_description"):
                    continue
                
                # Set defaults for missing fields
                failure.setdefault("frequency", "Occasionally")
                failure.setdefault("impact_description", "Impacto en operaciones")
                failure.setdefault("root_cause", None)
                failure.setdefault("current_workaround", None)
                failure.setdefault("recovery_time_minutes", None)
                failure.setdefault("proposed_prevention", None)
                failure.setdefault("related_process", None)
                failure.setdefault("confidence_score", 0.8)
                failure.setdefault("extraction_reasoning", "Extracted by LLM")
            
            return failures
            
        except Exception as e:
            print(f"Warning: LLM extraction failed: {e}")
            return []
    
    def _merge_failures(self, rule_based: List[Dict], llm_based: List[Dict]) -> List[Dict]:
        """Merge and deduplicate failures from different extraction methods"""
        merged = {}
        
        # Add rule-based failures
        for failure in rule_based:
            key = failure['failure_description'].lower()[:50]  # Use first 50 chars as key
            merged[key] = failure
        
        # Merge LLM failures (prefer LLM data if confidence is higher)
        for failure in llm_based:
            key = failure['failure_description'].lower()[:50]
            if key in merged:
                if failure.get("confidence_score", 0) > merged[key].get("confidence_score", 0):
                    merged[key] = failure
            else:
                merged[key] = failure
        
        return list(merged.values())



class EnhancedPainPointExtractor:
    """
    Extracts enhanced pain point entities with:
    - Intensity scoring (1-10)
    - Frequency classification
    - JTBD context (WHO, WHAT, WHERE)
    - Cost quantification
    - Hair-on-fire flagging
    """
    
    # Intensity language indicators
    INTENSITY_INDICATORS = {
        10: ["catastrófico", "crítico extremo", "imposible"],
        9: ["crítico", "bloqueante", "paraliza", "detiene todo"],
        8: ["urgente", "grave", "muy problemático", "serio"],
        7: ["importante", "significativo", "considerable"],
        6: ["problemático", "complicado", "dificulta"],
        5: ["molesto", "incómodo", "tedioso"],
        4: ["menor", "pequeño problema"],
        3: ["leve", "poco problema"],
        2: ["mínimo", "casi no afecta"],
        1: ["insignificante", "trivial"]
    }
    
    # Frequency keywords
    FREQUENCY_KEYWORDS = {
        "Daily": ["diario", "diaria", "cada día", "todos los días", "diariamente"],
        "Weekly": ["semanal", "cada semana", "semanalmente"],
        "Monthly": ["mensual", "cada mes", "mensualmente"],
        "Quarterly": ["trimestral", "cada trimestre"],
        "Annually": ["anual", "cada año", "anualmente"],
        "Ad-hoc": ["ocasional", "a veces", "cuando se necesita"]
    }
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract enhanced pain points from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of enhanced pain point entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text for analysis
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # Use LLM extraction (rule-based is too limited for this complex task)
        pain_points = self._llm_extraction(full_text, meta)
        
        # Post-process: calculate hair_on_fire flag and annual cost
        for pain in pain_points:
            self._calculate_hair_on_fire(pain)
            self._calculate_annual_cost(pain)
        
        return pain_points
    
    def _calculate_hair_on_fire(self, pain_point: Dict):
        """Calculate if this is a hair-on-fire problem"""
        intensity = pain_point.get("intensity_score", 0)
        frequency = pain_point.get("frequency", "")
        
        # Hair-on-fire: intensity >= 8 AND frequency is Daily or Weekly
        if intensity >= 8 and frequency in ["Daily", "Weekly"]:
            pain_point["hair_on_fire"] = True
        else:
            pain_point["hair_on_fire"] = False
    
    def _calculate_annual_cost(self, pain_point: Dict):
        """Calculate estimated annual cost"""
        time_wasted = pain_point.get("time_wasted_per_occurrence_minutes") or 0
        frequency = pain_point.get("frequency", "")
        cost_monthly = pain_point.get("cost_impact_monthly_usd") or 0
        
        # Estimate occurrences per year based on frequency
        occurrences_per_year = {
            "Daily": 250,  # Working days
            "Weekly": 52,
            "Monthly": 12,
            "Quarterly": 4,
            "Annually": 1,
            "Ad-hoc": 12  # Assume monthly
        }.get(frequency, 12)
        
        # Calculate time cost (assuming $30/hour average)
        hourly_rate = 30
        time_cost_annual = (time_wasted / 60) * hourly_rate * occurrences_per_year if time_wasted else 0
        
        # Add direct cost impact
        direct_cost_annual = cost_monthly * 12 if cost_monthly else 0
        
        # Total annual cost
        pain_point["estimated_annual_cost_usd"] = time_cost_annual + direct_cost_annual
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Use LLM to extract enhanced pain points"""
        
        if not self.client:
            return []
        
        prompt = f"""You are analyzing an interview to extract pain points with detailed context. Focus on identifying problems, their severity, frequency, who's affected, and the business impact.

**Interview Context:**
- Role: {meta.get('role', 'Unknown')}
- Company: {meta.get('company', 'Unknown')}

**Interview Text:**
{text[:4000]}

**Your Task:**
Extract ALL pain points - problems, frustrations, inefficiencies, or obstacles mentioned.

**For each pain point, extract:**

1. **description**: Clear description of the problem (e.g., "Conciliación manual entre sistemas toma 2 horas diarias")

2. **intensity_score**: Severity on scale 1-10:
   - 10: Catastrophic, blocks everything
   - 9: Critical, major blocker
   - 8: Urgent, serious problem
   - 7: Important, significant issue
   - 6: Problematic, complicates work
   - 5: Annoying, tedious
   - 4: Minor problem
   - 3: Light issue
   - 2: Minimal impact
   - 1: Insignificant

3. **frequency**: How often it occurs:
   - "Daily" - every day
   - "Weekly" - every week
   - "Monthly" - every month
   - "Quarterly" - every quarter
   - "Annually" - every year
   - "Ad-hoc" - occasionally

4. **jtbd_who**: WHO is affected (specific roles, e.g., "Gerente de Contabilidad", "Equipo de ventas")

5. **jtbd_what**: WHAT job they're trying to do (e.g., "Cerrar ventas del día", "Generar reporte mensual")

6. **jtbd_where**: WHERE in the process (e.g., "Durante cierre diario", "Al recibir solicitud")

7. **jtbd_formatted**: Format as "When [situation], I want to [goal], but [obstacle]"

8. **time_wasted_per_occurrence_minutes**: Time wasted each time (in minutes, e.g., 120 for 2 hours)

9. **cost_impact_monthly_usd**: Direct cost impact per month in USD (if mentioned)

10. **root_cause**: Why it happens (e.g., "Sistemas no integrados", "Falta de automatización")

11. **current_workaround**: How they work around it (e.g., "Entrada manual en Excel")

12. **affected_roles**: List of roles affected (e.g., ["Gerente", "Contador", "Asistente"])

13. **affected_processes**: List of processes affected (e.g., ["Cierre diario", "Conciliación"])

14. **severity**: High/Medium/Low (based on intensity_score: 8-10=High, 5-7=Medium, 1-4=Low)

15. **impact_description**: What happens because of this problem

16. **proposed_solutions**: Suggested solutions (if mentioned)

17. **confidence_score**: 0.0-1.0 based on how explicit the mention is

18. **extraction_reasoning**: Brief explanation

**Important Guidelines:**
- Extract SPECIFIC pain points, not vague complaints
- Quantify time and cost when mentioned
- Be specific about WHO is affected (roles, not "equipo")
- Identify root causes when mentioned or clearly implied
- Score intensity based on language used (crítico=9, urgente=8, molesto=5)
- Extract frequency from context (diario=Daily, semanal=Weekly)
- Format JTBD clearly with situation, goal, and obstacle

**Examples:**
- "La conciliación manual entre Opera y SAP toma 2 horas diarias" →
  - intensity: 7, frequency: Daily, time_wasted: 120
  - JTBD: "When closing daily sales, I want to reconcile systems automatically, but I have to do it manually for 2 hours"

- "Sistema se cae cada semana, perdemos ventas" →
  - intensity: 9, frequency: Weekly
  - JTBD: "When system crashes, I want to continue serving customers, but we lose sales"

**Return Format:**
{{
  "pain_points": [
    {{
      "description": "Clear description",
      "intensity_score": 1-10,
      "frequency": "Daily|Weekly|Monthly|Quarterly|Annually|Ad-hoc",
      "jtbd_who": "Specific role",
      "jtbd_what": "Job to be done",
      "jtbd_where": "Where in process",
      "jtbd_formatted": "When [situation], I want to [goal], but [obstacle]",
      "time_wasted_per_occurrence_minutes": number or null,
      "cost_impact_monthly_usd": number or null,
      "root_cause": "Why it happens or null",
      "current_workaround": "How they work around it or null",
      "affected_roles": ["Role 1", "Role 2"],
      "affected_processes": ["Process 1"],
      "severity": "High|Medium|Low",
      "impact_description": "What happens",
      "proposed_solutions": ["Solution 1"],
      "confidence_score": 0.0-1.0,
      "extraction_reasoning": "Brief explanation"
    }}
  ]
}}

If no pain points found, return {{"pain_points": []}}.
"""
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert business analyst specializing in identifying operational pain points, quantifying their impact, and understanding the jobs-to-be-done context. Always return valid JSON."
                },
                {"role": "user", "content": prompt}
            ]
            
            response_content = call_llm_with_fallback(self.client, messages, temperature=0.1)
            
            if not response_content:
                print("Warning: All LLM models failed for pain point extraction")
                return []
            
            result = json.loads(response_content)
            pain_points = result.get("pain_points", [])
            
            # Add extraction source and validate
            for pain in pain_points:
                pain["extraction_source"] = "llm_extraction"
                
                # Ensure required fields exist
                if not pain.get("description"):
                    continue
                
                # Set defaults for missing fields
                pain.setdefault("intensity_score", 5)
                pain.setdefault("frequency", "Ad-hoc")
                pain.setdefault("jtbd_who", meta.get("role", "Unknown"))
                pain.setdefault("jtbd_what", "Realizar trabajo")
                pain.setdefault("jtbd_where", "Durante proceso")
                pain.setdefault("jtbd_formatted", f"When working, I want to be efficient, but {pain['description']}")
                pain.setdefault("time_wasted_per_occurrence_minutes", None)
                pain.setdefault("cost_impact_monthly_usd", None)
                pain.setdefault("root_cause", None)
                pain.setdefault("current_workaround", None)
                pain.setdefault("affected_roles", [meta.get("role", "Unknown")])
                pain.setdefault("affected_processes", [])
                pain.setdefault("severity", "Medium")
                pain.setdefault("impact_description", "Afecta operaciones")
                pain.setdefault("proposed_solutions", [])
                pain.setdefault("confidence_score", 0.8)
                pain.setdefault("extraction_reasoning", "Extracted by LLM")
                
                # Ensure type is set
                pain.setdefault("type", "Process Inefficiency")
            
            return pain_points
            
        except Exception as e:
            print(f"Warning: LLM extraction failed: {e}")
            return []



class AutomationCandidateExtractor:
    """Extracts enhanced automation candidate entities with effort/impact scoring and priority matrix classification"""
    
    # Priority quadrants based on effort and impact scores
    PRIORITY_QUADRANTS = {
        "Quick Win": "Low effort (1-2), High impact (4-5)",
        "Strategic": "High effort (4-5), High impact (4-5)",
        "Incremental": "Low effort (1-2), Low impact (1-3)",
        "Reconsider": "High effort (4-5), Low impact (1-3)"
    }
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract enhanced automation candidate entities from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of enhanced automation candidate entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text for analysis
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # Extract automation candidates using LLM
        candidates = self._llm_extraction(full_text, meta)
        
        # Enhance each candidate with effort/impact scoring and priority classification
        for candidate in candidates:
            candidate["effort_score"] = self._calculate_effort_score(candidate)
            candidate["impact_score"] = self._calculate_impact_score(candidate)
            candidate["priority_quadrant"] = self._classify_priority_quadrant(
                candidate["effort_score"], 
                candidate["impact_score"]
            )
            
            # Calculate ROI if cost savings available
            if candidate.get("estimated_annual_savings_usd") and candidate.get("implementation_cost_usd"):
                candidate["estimated_roi_months"] = self._calculate_roi_months(
                    candidate["estimated_annual_savings_usd"],
                    candidate["implementation_cost_usd"]
                )
        
        return candidates
    
    def _calculate_effort_score(self, candidate: Dict) -> int:
        """
        Calculate effort score (1-5) based on complexity and systems involved
        
        1 = Very Low: Single system, simple automation
        2 = Low: 2 systems, moderate complexity
        3 = Medium: 3 systems, moderate complexity
        4 = High: 4+ systems, high complexity
        5 = Very High: 5+ systems, very high complexity
        """
        score = 1
        
        # Factor 1: Number of systems involved
        systems_involved = candidate.get("systems_involved", [])
        if isinstance(systems_involved, list):
            num_systems = len(systems_involved)
        else:
            num_systems = len(str(systems_involved).split(","))
        
        if num_systems >= 5:
            score += 2
        elif num_systems >= 3:
            score += 1
        elif num_systems >= 2:
            score += 0.5
        
        # Factor 2: Complexity rating
        complexity = candidate.get("complexity", "").lower()
        if "high" in complexity or "complex" in complexity:
            score += 1.5
        elif "medium" in complexity or "moderate" in complexity:
            score += 0.5
        
        # Factor 3: Data integration requirements
        data_sources = candidate.get("data_sources_needed", [])
        if isinstance(data_sources, list):
            if len(data_sources) >= 3:
                score += 1
        
        # Factor 4: Approval requirements (adds complexity)
        if candidate.get("approval_required"):
            score += 0.5
        
        # Cap at 5
        return min(5, max(1, int(round(score))))
    
    def _calculate_impact_score(self, candidate: Dict) -> int:
        """
        Calculate impact score (1-5) based on pain point severity, frequency, and affected roles
        
        1 = Very Low: Minor improvement, few people affected
        2 = Low: Small improvement, limited scope
        3 = Medium: Moderate improvement, some people affected
        4 = High: Significant improvement, many people affected
        5 = Very High: Major improvement, organization-wide impact
        """
        score = 1
        
        # Factor 1: Pain point severity/intensity
        # Look for related pain point data
        impact_desc = candidate.get("impact", "").lower()
        if any(word in impact_desc for word in ["critical", "crítico", "urgente", "bloqueante"]):
            score += 2
        elif any(word in impact_desc for word in ["high", "alto", "importante", "significativo"]):
            score += 1.5
        elif any(word in impact_desc for word in ["medium", "medio", "moderado"]):
            score += 0.5
        
        # Factor 2: Time savings
        time_saved = candidate.get("time_wasted_per_occurrence_minutes", 0)
        if time_saved >= 120:  # 2+ hours
            score += 1.5
        elif time_saved >= 60:  # 1+ hour
            score += 1
        elif time_saved >= 30:  # 30+ minutes
            score += 0.5
        
        # Factor 3: Frequency
        frequency = candidate.get("frequency", "").lower()
        if "daily" in frequency or "diario" in frequency or "continuo" in frequency:
            score += 1.5
        elif "weekly" in frequency or "semanal" in frequency:
            score += 1
        elif "monthly" in frequency or "mensual" in frequency:
            score += 0.5
        
        # Factor 4: Cost savings
        cost_savings = candidate.get("estimated_annual_savings_usd") or 0
        if cost_savings >= 50000:
            score += 1.5
        elif cost_savings >= 20000:
            score += 1
        elif cost_savings >= 10000:
            score += 0.5
        
        # Factor 5: Number of affected roles
        affected_roles = candidate.get("affected_roles", [])
        if isinstance(affected_roles, list):
            if len(affected_roles) >= 5:
                score += 1
            elif len(affected_roles) >= 3:
                score += 0.5
        
        # Cap at 5
        return min(5, max(1, int(round(score))))
    
    def _classify_priority_quadrant(self, effort: int, impact: int) -> str:
        """
        Classify automation candidate into priority quadrant
        
        Quick Win: Low effort (1-2), High impact (4-5)
        Strategic: High effort (4-5), High impact (4-5)
        Incremental: Low effort (1-2), Low impact (1-3)
        Reconsider: High effort (4-5), Low impact (1-3)
        """
        if effort <= 2 and impact >= 4:
            return "Quick Win"
        elif effort >= 4 and impact >= 4:
            return "Strategic"
        elif effort <= 2 and impact <= 3:
            return "Incremental"
        elif effort >= 4 and impact <= 3:
            return "Reconsider"
        else:
            # Medium effort (3) - classify based on impact
            if impact >= 4:
                return "Strategic"
            else:
                return "Incremental"
    
    def _calculate_roi_months(self, annual_savings: float, implementation_cost: float) -> float:
        """
        Calculate ROI in months
        
        ROI (months) = (Implementation Cost / Annual Savings) * 12
        """
        if annual_savings <= 0:
            return None
        
        return round((implementation_cost / annual_savings) * 12, 1)
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Use LLM to extract automation candidates with monitoring and approval requirements"""
        
        if not self.client:
            return []
        
        prompt = f"""You are analyzing an interview to extract automation opportunities. Focus on identifying manual processes that could be automated, along with their current workarounds, data requirements, and approval needs.

**Interview Context:**
- Role: {meta.get('role', 'Unknown')}
- Company: {meta.get('company', 'Unknown')}

**Interview Text:**
{text[:4000]}

**Your Task:**
Extract ALL automation opportunities mentioned or implied. An automation candidate exists when:
1. A manual process is described that could be automated
2. A repetitive task is mentioned
3. A pain point involves manual data entry, reconciliation, or coordination
4. Someone mentions "debería ser automático" or similar
5. A workaround exists that could be replaced with automation

**For each automation candidate, extract:**

1. **name**: Descriptive name for the automation (e.g., "Integración automática Opera-SAP", "Bot de WhatsApp para consultas frecuentes")
2. **process**: Business process being automated (e.g., "Cierre diario de ventas", "Gestión de solicitudes de mantenimiento")
3. **trigger_event**: What triggers the automation (e.g., "Cierre de turno en POS", "Recepción de solicitud por WhatsApp")
4. **action**: What the automation does (e.g., "Transferir ventas automáticamente a SAP", "Responder consultas frecuentes")
5. **output**: Expected result (e.g., "Reporte de ventas consolidado", "Respuesta inmediata al cliente")
6. **owner**: Who would own/manage this automation (role from interview or inferred)
7. **complexity**: "Low", "Medium", or "High" based on technical complexity
8. **impact**: "Low", "Medium", or "High" based on business impact
9. **effort_estimate**: Rough estimate if mentioned (e.g., "2-3 months", "1 week")
10. **systems_involved**: List of systems that need to be integrated (e.g., ["Simphony POS", "SAP", "Opera PMS"])
11. **current_manual_process_description**: How it's done manually now (e.g., "Exportar de cada sistema, conciliar en Excel, importar manualmente")
12. **data_sources_needed**: Systems/APIs needed for data (e.g., ["Simphony API", "SAP API"])
13. **approval_required**: true if this automation would need approval workflow, false otherwise
14. **approval_threshold_usd**: Dollar amount requiring approval if mentioned
15. **monitoring_metrics**: List of metrics to monitor (e.g., ["Tiempo de conciliación", "Tasa de error", "Disponibilidad"])
16. **time_wasted_per_occurrence_minutes**: Time currently wasted per occurrence
17. **frequency**: How often this happens ("Daily", "Weekly", "Monthly", "Ad-hoc")
18. **estimated_annual_savings_usd**: Estimated annual cost savings if calculable
19. **affected_roles**: List of roles that would benefit (e.g., ["Gerente de Restaurantes", "Contador"])
20. **confidence_score**: 0.0-1.0 based on how explicit the opportunity is
21. **extraction_reasoning**: Brief explanation

**Important Guidelines:**
- Extract both explicitly mentioned automations AND implied opportunities
- Be specific about what would be automated (not just "automatizar proceso")
- Identify current workarounds that could be eliminated
- Note data sources and APIs needed for integration
- Determine if approval workflows are needed (financial transactions, critical operations)
- Suggest monitoring metrics for the automation
- Calculate time/cost savings if information is available
- Complexity: Low = single system, simple logic; Medium = 2-3 systems, moderate logic; High = 4+ systems, complex logic

**Examples of Automation Candidates:**
- "Paso datos de Simphony a SAP manualmente cada día, toma 2 horas" → Automation: "Integración automática Simphony-SAP"
- "Respondo las mismas preguntas por WhatsApp todo el tiempo" → Automation: "Bot de WhatsApp para consultas frecuentes"
- "Tengo que revisar inventario manualmente y hacer pedidos" → Automation: "Sistema de alertas de stock mínimo con pedidos automáticos"

**Return Format:**
{{
  "automation_candidates": [
    {{
      "name": "Automation name",
      "process": "Business process",
      "trigger_event": "What triggers it",
      "action": "What it does",
      "output": "Expected result",
      "owner": "Role",
      "complexity": "Low|Medium|High",
      "impact": "Low|Medium|High",
      "effort_estimate": "Time estimate or null",
      "systems_involved": ["System 1", "System 2"],
      "current_manual_process_description": "How it's done now",
      "data_sources_needed": ["API 1", "API 2"],
      "approval_required": true|false,
      "approval_threshold_usd": number or null,
      "monitoring_metrics": ["Metric 1", "Metric 2"],
      "time_wasted_per_occurrence_minutes": number or null,
      "frequency": "Daily|Weekly|Monthly|Ad-hoc",
      "estimated_annual_savings_usd": number or null,
      "affected_roles": ["Role 1", "Role 2"],
      "confidence_score": 0.0-1.0,
      "extraction_reasoning": "Brief explanation"
    }}
  ]
}}

If no automation candidates are found, return {{"automation_candidates": []}}.
"""
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert in business process automation, RPA, and digital transformation. You identify automation opportunities, assess their complexity and impact, and design monitoring strategies. Always return valid JSON."
                },
                {"role": "user", "content": prompt}
            ]
            
            response_content = call_llm_with_fallback(self.client, messages, temperature=0.1)
            
            if not response_content:
                print("Warning: All LLM models failed for automation candidate extraction")
                return []
            
            result = json.loads(response_content)
            candidates = result.get("automation_candidates", [])
            
            # Validate and set defaults
            for candidate in candidates:
                if not candidate.get("name"):
                    continue
                
                # Set defaults for missing fields
                candidate.setdefault("process", "Unknown")
                candidate.setdefault("trigger_event", "Manual trigger")
                candidate.setdefault("action", "Automate manual process")
                candidate.setdefault("output", "Automated result")
                candidate.setdefault("owner", meta.get("role", "Unknown"))
                candidate.setdefault("complexity", "Medium")
                candidate.setdefault("impact", "Medium")
                candidate.setdefault("effort_estimate", None)
                candidate.setdefault("systems_involved", [])
                candidate.setdefault("current_manual_process_description", "")
                candidate.setdefault("data_sources_needed", [])
                candidate.setdefault("approval_required", False)
                candidate.setdefault("approval_threshold_usd", None)
                candidate.setdefault("monitoring_metrics", [])
                candidate.setdefault("time_wasted_per_occurrence_minutes", None)
                candidate.setdefault("frequency", "Ad-hoc")
                candidate.setdefault("estimated_annual_savings_usd", None)
                candidate.setdefault("affected_roles", [meta.get("role", "Unknown")])
                candidate.setdefault("confidence_score", 0.8)
                candidate.setdefault("extraction_reasoning", "Extracted by LLM")
                candidate["extraction_source"] = "llm_extraction"
            
            return candidates
            
        except Exception as e:
            print(f"Warning: LLM extraction failed: {e}")
            return []



class TeamStructureExtractor:
    """Extracts team structure entities from interview text"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract team structure from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of team structure entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # Use LLM to extract team structure
        team_structures = self._llm_extraction(full_text, meta)
        
        return team_structures
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Extract team structure using LLM"""
        if not self.client:
            return []
        
        prompt = f"""Extract team structure information from this interview.

Interview with: {meta.get('role', 'Unknown')} at {meta.get('company', 'Unknown')}

Interview text:
{text[:3000]}

Extract:
1. Role/position of the interviewee
2. Team size (number of people they work with or manage)
3. Who they report to (boss/manager)
4. Who they coordinate with (other departments/roles)
5. External dependencies (vendors, partners they work with)

Return as JSON array with this structure:
[{{
    "role": "specific role",
    "team_size": number or null,
    "reports_to": "role they report to" or null,
    "coordinates_with": ["role1", "role2"],
    "external_dependencies": ["vendor1", "partner1"],
    "confidence_score": 0.0-1.0,
    "extraction_reasoning": "why extracted"
}}]

If no team structure info found, return empty array []."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            team_structures = result.get("team_structures", [])
            
            # Add metadata
            for ts in team_structures:
                ts["extraction_source"] = "llm"
                if ts.get("confidence_score", 0) < 0.7:
                    ts["needs_review"] = True
            
            return team_structures
            
        except Exception as e:
            print(f"Error in LLM extraction: {e}")
            return []


class KnowledgeGapExtractor:
    """Extracts knowledge gap entities from interview text"""
    
    # Keywords indicating knowledge gaps
    GAP_KEYWORDS = [
        "no sé", "no sabemos", "no conozco", "desconozco",
        "falta capacitación", "necesitamos training", "no entiendo",
        "no está claro", "confuso", "complicado de entender",
        "necesito aprender", "no me enseñaron", "falta conocimiento"
    ]
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract knowledge gaps from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of knowledge gap entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # Check if there are any gap keywords
        text_lower = full_text.lower()
        has_gaps = any(keyword in text_lower for keyword in self.GAP_KEYWORDS)
        
        if not has_gaps:
            return []
        
        # Use LLM to extract knowledge gaps
        knowledge_gaps = self._llm_extraction(full_text, meta)
        
        return knowledge_gaps
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Extract knowledge gaps using LLM"""
        if not self.client:
            return []
        
        prompt = f"""Extract knowledge gaps and training needs from this interview.

Interview with: {meta.get('role', 'Unknown')} at {meta.get('company', 'Unknown')}

Interview text:
{text[:3000]}

Look for:
1. Things they don't know or understand
2. Training needs mentioned
3. Skills gaps
4. Confusion about processes or systems
5. Areas where they need help

Return as JSON array:
[{{
    "area": "what they don't know/understand",
    "affected_roles": ["role1", "role2"],
    "impact": "how this affects their work",
    "training_needed": "what training would help",
    "confidence_score": 0.0-1.0,
    "extraction_reasoning": "why extracted"
}}]

If no knowledge gaps found, return empty array []."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            gaps = result.get("knowledge_gaps", [])
            
            # Add metadata
            for gap in gaps:
                gap["extraction_source"] = "llm"
                if gap.get("confidence_score", 0) < 0.7:
                    gap["needs_review"] = True
            
            return gaps
            
        except Exception as e:
            print(f"Error in LLM extraction: {e}")
            return []


class SuccessPatternExtractor:
    """Extracts success pattern entities from interview text"""
    
    # Keywords indicating success
    SUCCESS_KEYWORDS = [
        "funciona bien", "funciona muy bien", "está funcionando",
        "me gusta", "nos gusta", "es bueno", "es excelente",
        "eficiente", "rápido", "fácil", "simple",
        "mejor práctica", "best practice", "éxito",
        "logro", "achievement", "bien hecho"
    ]
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract success patterns from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of success pattern entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # Check if there are any success keywords
        text_lower = full_text.lower()
        has_success = any(keyword in text_lower for keyword in self.SUCCESS_KEYWORDS)
        
        if not has_success:
            return []
        
        # Use LLM to extract success patterns
        success_patterns = self._llm_extraction(full_text, meta)
        
        return success_patterns
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Extract success patterns using LLM"""
        if not self.client:
            return []
        
        prompt = f"""Extract success patterns and best practices from this interview.

Interview with: {meta.get('role', 'Unknown')} at {meta.get('company', 'Unknown')}

Interview text:
{text[:3000]}

Look for:
1. Things that work well
2. Best practices
3. Successful processes or systems
4. Positive outcomes
5. Things they're proud of

Return as JSON array:
[{{
    "pattern": "what works well",
    "role": "who does this",
    "benefit": "why it works/what benefit it provides",
    "replicable_to": ["where else this could be applied"],
    "confidence_score": 0.0-1.0,
    "extraction_reasoning": "why extracted"
}}]

If no success patterns found, return empty array []."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            patterns = result.get("success_patterns", [])
            
            # Add metadata
            for pattern in patterns:
                pattern["extraction_source"] = "llm"
                if pattern.get("confidence_score", 0) < 0.7:
                    pattern["needs_review"] = True
            
            return patterns
            
        except Exception as e:
            print(f"Error in LLM extraction: {e}")
            return []


class BudgetConstraintExtractor:
    """Extracts budget constraint entities from interview text"""
    
    # Keywords indicating budget constraints
    BUDGET_KEYWORDS = [
        "presupuesto", "budget", "costo", "cost", "precio", "price",
        "aprobación", "approval", "autorización", "authorization",
        "límite", "limit", "tope", "máximo", "maximum",
        "$", "USD", "Bs", "bolivianos", "dólares", "dollars"
    ]
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract budget constraints from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of budget constraint entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # Check if there are any budget keywords
        text_lower = full_text.lower()
        has_budget = any(keyword in text_lower for keyword in self.BUDGET_KEYWORDS)
        
        if not has_budget:
            return []
        
        # Use LLM to extract budget constraints
        budget_constraints = self._llm_extraction(full_text, meta)
        
        return budget_constraints
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Extract budget constraints using LLM"""
        if not self.client:
            return []
        
        prompt = f"""Extract budget constraints and approval thresholds from this interview.

Interview with: {meta.get('role', 'Unknown')} at {meta.get('company', 'Unknown')}

Interview text:
{text[:3000]}

Look for:
1. Budget limits or constraints
2. Approval thresholds (amounts requiring approval)
3. Who approves what amounts
4. Budget-related pain points
5. Spending authority limits

Return as JSON array:
[{{
    "area": "what the budget is for",
    "budget_type": "operational/capital/project/etc",
    "approval_required_above": amount in USD or null,
    "approver": "who approves",
    "pain_point": "any budget-related problems",
    "confidence_score": 0.0-1.0,
    "extraction_reasoning": "why extracted"
}}]

If no budget constraints found, return empty array []."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            constraints = result.get("budget_constraints", [])
            
            # Add metadata
            for constraint in constraints:
                constraint["extraction_source"] = "llm"
                if constraint.get("confidence_score", 0) < 0.7:
                    constraint["needs_review"] = True
            
            return constraints
            
        except Exception as e:
            print(f"Error in LLM extraction: {e}")
            return []


class ExternalDependencyExtractor:
    """Extracts external dependency entities from interview text"""
    
    # Keywords indicating external dependencies
    EXTERNAL_KEYWORDS = [
        "proveedor", "vendor", "supplier", "tercero", "third party",
        "contratista", "contractor", "partner", "socio",
        "externo", "external", "outsource", "subcontrata"
    ]
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize extractor with OpenAI client"""
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
    
    def extract_from_interview(self, interview_data: Dict) -> List[Dict]:
        """
        Extract external dependencies from interview data
        
        Args:
            interview_data: Dict with 'meta' and 'qa_pairs'
            
        Returns:
            List of external dependency entities
        """
        meta = interview_data.get("meta", {})
        qa_pairs = interview_data.get("qa_pairs", {})
        
        # Combine all Q&A into text
        full_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs.items()])
        
        # Check if there are any external keywords
        text_lower = full_text.lower()
        has_external = any(keyword in text_lower for keyword in self.EXTERNAL_KEYWORDS)
        
        if not has_external:
            return []
        
        # Use LLM to extract external dependencies
        external_deps = self._llm_extraction(full_text, meta)
        
        return external_deps
    
    def _llm_extraction(self, text: str, meta: Dict) -> List[Dict]:
        """Extract external dependencies using LLM"""
        if not self.client:
            return []
        
        prompt = f"""Extract external dependencies (vendors, partners, contractors) from this interview.

Interview with: {meta.get('role', 'Unknown')} at {meta.get('company', 'Unknown')}

Interview text:
{text[:3000]}

Look for:
1. Vendor names and what they provide
2. Service providers
3. Partners or contractors
4. How often they interact
5. Who coordinates with them
6. SLAs or service agreements
7. Payment processes

Return as JSON array:
[{{
    "vendor": "vendor/partner name",
    "service": "what they provide",
    "frequency": "how often used (Daily/Weekly/Monthly/etc)",
    "coordinator": "who manages this relationship",
    "sla": "service level agreement if mentioned",
    "payment_process": "how payments are handled",
    "confidence_score": 0.0-1.0,
    "extraction_reasoning": "why extracted"
}}]

If no external dependencies found, return empty array []."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            deps = result.get("external_dependencies", [])
            
            # Add metadata
            for dep in deps:
                dep["extraction_source"] = "llm"
                if dep.get("confidence_score", 0) < 0.7:
                    dep["needs_review"] = True
            
            return deps
            
        except Exception as e:
            print(f"Error in LLM extraction: {e}")
            return []
