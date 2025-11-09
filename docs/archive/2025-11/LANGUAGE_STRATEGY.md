# Language Strategy: Spanish-First Approach

## Decision: Keep Everything in Spanish

### Why Spanish-First?

1. **Source Data is Spanish**: All 44 interviews are in Spanish
2. **GPT-4 is Excellent at Spanish**: No accuracy loss
3. **Preserves Nuance**: "Urgente" ≠ "Urgent" (cultural context matters)
4. **Users Think in Spanish**: Managers will query in Spanish
5. **No Translation Errors**: Avoid information loss in translation

### What Stays in Spanish

**Database Fields (Spanish):**
```json
{
  "descripcion": "Conciliación manual entre Opera, Simphony y SAP",
  "tipo": "Ineficiencia de Proceso",
  "frecuencia": "Diario",
  "severidad": "Alta",
  "solucion_propuesta": "Integración automática entre sistemas"
}
```

**Extraction Prompts (Spanish):**
```
Analiza esta entrevista y extrae los puntos de dolor (pain points).

Un punto de dolor es:
- Un problema recurrente que dificulta el trabajo
- Una ineficiencia que causa frustración
- Un obstáculo que impide cumplir objetivos

Responde en JSON en ESPAÑOL.
```

**Query Interface (Bilingual):**
```python
# Users can query in Spanish
results = db.query("Muéstrame todos los puntos de dolor críticos en Restaurantes")

# Or English (GPT-4 translates internally)
results = db.query("Show me all critical pain points in Restaurants")
```

### What Can Be in English

**Code & Schema (English):**
```python
class PainPoint:
    """Pain point entity - keeps data in Spanish"""
    descripcion: str  # Spanish text
    tipo: str  # Spanish enum
    severidad: str  # Spanish enum
```

**Documentation (English):**
- Technical docs for developers
- Architecture diagrams
- API documentation

**Reports (Bilingual):**
- Executive summaries in Spanish
- Technical details can be English
- Charts/graphs with Spanish labels

## Implementation Changes

### 1. Update Extraction Prompts to Spanish

**Current (English):**
```python
system_prompt = """You are an expert business process analyst.
Extract PAIN POINTS from manager interviews.

A pain point is:
- A recurring problem that hinders work
- An inefficiency causing frustration
- An obstacle preventing goal achievement

Respond in JSON with this format:
{
  "pain_points": [
    {
      "type": "Process|Data|Systems|Culture",
      "description": "Clear description of the problem",
      ...
    }
  ]
}"""
```

**New (Spanish):**
```python
system_prompt = """Eres un analista experto en procesos empresariales.
Extrae PUNTOS DE DOLOR de entrevistas a gerentes.

Un punto de dolor es:
- Un problema recurrente que dificulta el trabajo
- Una ineficiencia que causa frustración
- Un obstáculo que impide cumplir objetivos

Responde en JSON en ESPAÑOL con este formato:
{
  "puntos_de_dolor": [
    {
      "tipo": "Proceso|Datos|Sistemas|Cultura",
      "descripcion": "Descripción clara del problema",
      "roles_afectados": ["Rol1", "Rol2"],
      "procesos_afectados": ["Proceso1"],
      "frecuencia": "Diario|Semanal|Mensual|Ocasional",
      "severidad": "Baja|Media|Alta|Crítica",
      "impacto": "Cómo afecta al trabajo",
      "soluciones_propuestas": ["Solución sugerida"]
    }
  ]
}"""
```

### 2. Update Database Schema (Keep Spanish Values)

**Field Names (English for code):**
```sql
CREATE TABLE pain_points (
    id INTEGER PRIMARY KEY,
    description TEXT,  -- Spanish text
    type TEXT,  -- Spanish enum
    severity TEXT,  -- Spanish enum
    ...
)
```

**Enum Values (Spanish):**
```python
SEVERITY_VALUES = ["Baja", "Media", "Alta", "Crítica"]
FREQUENCY_VALUES = ["Diario", "Semanal", "Mensual", "Ocasional"]
TYPE_VALUES = ["Proceso", "Datos", "Sistemas", "Cultura", "Capacitación", "Aprobación", "Integración"]
```

### 3. Bilingual Query Interface

**For AI Agents (Spanish or English):**
```python
class BilingualQueryInterface:
    def query(self, question: str, language: str = "auto") -> List[Dict]:
        """
        Query in Spanish or English, returns results in original language
        
        Examples:
            query("¿Cuáles son los puntos de dolor críticos?")
            query("What are the critical pain points?")
        """
        # Detect language
        if language == "auto":
            language = detect_language(question)
        
        # Translate query to SQL (GPT-4 handles both languages)
        sql = self._translate_to_sql(question, language)
        
        # Execute query
        results = self.db.execute(sql)
        
        # Return in original language
        return results
```

### 4. Reports (Bilingual)

**Executive Summary (Spanish):**
```markdown
# Resumen Ejecutivo: Validación de Prioridades del CEO

## Prioridades Confirmadas (Alto Soporte de Datos)
✅ **Reportes y KPIs Inteligentes** - 68% de soporte
   - Mencionado en 30 de 44 entrevistas
   - Severidad promedio: Alta
   - Costo estimado: $50,000/año en tiempo perdido

## Prioridades Débiles (Bajo Soporte de Datos)
⚠️ **Gestión de Energía** - 12% de soporte
   - Mencionado en 5 de 44 entrevistas
   - Severidad promedio: Media
   - Recomendación: Revisar prioridad

## Oportunidades Pasadas por Alto
🆕 **Conciliación Manual entre Sistemas** - 45% frecuencia
   - NO está en lista del CEO
   - Mencionado en 20 de 44 entrevistas
   - Costo estimado: $120,000/año
   - Recomendación: Agregar a prioridades
```

**Technical Details (English OK):**
```markdown
## Data Support Calculation Methodology

Data support score = (interviews_mentioning / total_interviews)

Thresholds:
- High support: >= 0.5 (50%)
- Medium support: 0.3 - 0.5 (30-50%)
- Low support: < 0.3 (30%)
```

## Benefits of Spanish-First

1. **Accuracy**: No translation errors
2. **Speed**: No translation step needed
3. **Cultural Context**: Preserves local terminology
4. **User Experience**: Managers query in their language
5. **Compliance**: Data stays in original language for audit

## When to Translate

**Only translate for:**
- External stakeholders who don't speak Spanish
- Integration with English-only systems
- Academic publications

**How to translate:**
```python
def translate_for_export(entity: Dict, target_language: str = "en") -> Dict:
    """Translate entity for export (on-demand)"""
    if target_language == "es":
        return entity  # Already in Spanish
    
    # Use GPT-4 for high-quality translation
    translated = gpt4_translate(entity, target_language)
    
    # Keep original in metadata
    translated["_original_language"] = "es"
    translated["_original_text"] = entity
    
    return translated
```

## Updated Extraction Pipeline

```python
# Spanish-first extraction
def extract_entities_spanish(interview: Dict) -> ExtractionResult:
    """Extract entities keeping everything in Spanish"""
    
    # Spanish prompt
    system_prompt = load_prompt("extraction_prompts_spanish.txt")
    
    # Extract in Spanish
    result = gpt4_extract(
        interview_text=interview["qa_pairs"],
        system_prompt=system_prompt,
        response_language="es"
    )
    
    # Validate Spanish enums
    validate_spanish_enums(result)
    
    return result
```

## Migration from Current Code

**What to change:**
1. ✅ Update all extraction prompts to Spanish
2. ✅ Change enum values to Spanish
3. ✅ Update validation rules for Spanish values
4. ✅ Keep database field names in English (code convention)
5. ✅ Add bilingual query interface

**What NOT to change:**
1. ❌ Code (stays in English)
2. ❌ Database field names (stays in English)
3. ❌ Technical documentation (stays in English)
4. ❌ Architecture diagrams (stays in English)

## Example: Pain Point in Spanish

```json
{
  "id": 1,
  "interview_id": 1,
  "company_name": "Hotel Los Tajibos",
  "business_unit": "Alimentos y Bebidas",
  "department": "Restaurantes",
  
  "tipo": "Ineficiencia de Proceso",
  "descripcion": "Conciliación manual entre Opera, Simphony y SAP toma 2 horas diarias",
  "roles_afectados": ["Gerente de Restaurantes", "Contador"],
  "procesos_afectados": ["Cierre diario de ventas"],
  "frecuencia": "Diario",
  "severidad": "Alta",
  "impacto": "Retraso en reportes, errores de conciliación, tiempo perdido",
  "soluciones_propuestas": ["Integración automática entre sistemas"],
  
  "intensidad": 8,
  "pelo_en_fuego": true,
  "tiempo_perdido_por_ocurrencia_minutos": 120,
  "costo_impacto_mensual_usd": 2000,
  "costo_anual_estimado_usd": 24000,
  
  "causa_raiz": "Sistemas no integrados, doble entrada manual",
  "solucion_actual": "Exportar de cada sistema y conciliar en Excel",
  
  "confidence_score": 0.95,
  "needs_review": false,
  "extraction_source": "interview_1_question_5"
}
```

## Recommendation

**Keep everything in Spanish except:**
- Code (English)
- Technical docs (English)
- Database field names (English)

**This gives you:**
- Maximum accuracy
- Cultural context preserved
- Easy for users to query
- Standard code conventions
