# OCR Module - Task 4: OCR Engine & Review CLI

Módulo de OCR con Mistral Pixtral (primario) + Tesseract (fallback) para extracción de texto multi-formato.

## Componentes

### 1. MistralPixtralClient
**Archivo:** `mistral_pixtral_client.py`

Cliente OCR primario usando Mistral Pixtral con soporte completo de español.

**Características:**
- Codificación base64 de imágenes
- Prompts específicos en español para documentos manuscritos/impresos/generales
- Estimación heurística de confianza
- Manejo de errores con mensajes en español
- Captura de metadata (modelo, tipo de documento, tamaño de imagen)

**Uso:**
```python
from intelligence_capture.ocr import MistralPixtralClient

client = MistralPixtralClient()  # Requiere MISTRAL_API_KEY

result = client.extract_text(
    Path('documento.jpg'),
    language='es',
    document_type='handwritten'  # 'printed', 'handwritten', 'general'
)

print(f"Texto: {result['text']}")
print(f"Confianza: {result['confidence']:.2f}")
print(f"Motor: {result['ocr_engine']}")
```

**Requisitos:**
- Variable de entorno `MISTRAL_API_KEY`
- Conexión a internet para API Mistral

---

### 2. TesseractFallback
**Archivo:** `tesseract_fallback.py`

Cliente OCR de fallback usando Tesseract para extracción de bajo costo.

**Características:**
- Verificación de instalación de Tesseract
- Extracción de cajas delimitadoras con puntuaciones de confianza
- Modo de extracción simple (solo texto)
- Consulta de idiomas disponibles
- Soporte de idioma español (spa)

**Uso:**
```python
from intelligence_capture.ocr import TesseractFallback

client = TesseractFallback()

# Extracción completa con metadata
result = client.extract_text(
    Path('documento.png'),
    language='spa'
)

# Extracción simple (más rápida)
text = client.extract_text_simple(Path('documento.png'))

# Verificar idiomas disponibles
langs = client.get_available_languages()
print(f"Idiomas: {langs}")
```

**Requisitos:**
- Tesseract instalado en el sistema:
  - macOS: `brew install tesseract tesseract-lang`
  - Ubuntu: `apt-get install tesseract-ocr tesseract-ocr-spa`
- Modelo de idioma español instalado

---

### 3. OCRCoordinator
**Archivo:** `ocr_coordinator.py`

Coordinador OCR con rate limiting y cola de revisión.

**Características:**
- Integración de rate limiter (máx 5 llamadas OCR concurrentes)
- Cadena de fallback Mistral Pixtral → Tesseract
- Inscripción automática en cola de revisión para segmentos de baja confianza
- Procesamiento de documentos multi-página
- Seguimiento de estadísticas (tasa de éxito, tasa de revisión)
- Clasificación de tipo de segmento (manuscrito, impreso degradado, tablas, mixto)

**Uso:**
```python
from intelligence_capture.ocr import OCRCoordinator
import asyncpg

# Conectar a PostgreSQL
conn = await asyncpg.connect(DATABASE_URL)

# Inicializar coordinador
coordinator = OCRCoordinator(conn)

# Procesar imagen individual
result = coordinator.process_image(
    Path('pagina_3.jpg'),
    document_id='550e8400-e29b-41d4-a716-446655440000',
    page_number=3,
    document_type='handwritten'
)

# Procesar documento completo
image_paths = [Path(f'page_{i}.jpg') for i in range(1, 11)]
results = coordinator.process_document(
    image_paths,
    document_id='550e8400-e29b-41d4-a716-446655440000',
    document_type='general'
)

# Estadísticas
stats = coordinator.get_stats()
print(f"Tasa de éxito: {stats['success_rate']:.1%}")
print(f"Tasa de revisión: {stats['review_rate']:.1%}")
print(f"Mistral exitoso: {stats['mistral_success']}")
print(f"Fallback Tesseract: {stats['tesseract_fallback']}")
```

**Umbrales de Confianza:**
- Manuscrito: `< 0.70` → cola de revisión
- Impreso: `< 0.90` → cola de revisión

**Requisitos:**
- Conexión asyncpg a PostgreSQL
- Tabla `ocr_review_queue` creada (ver `scripts/migrations/2025_01_02_ocr_review_queue.sql`)

---

### 4. OCR Reviewer CLI
**Archivo:** `ocr_reviewer_cli.py`

CLI interactiva para revisión manual de segmentos OCR de baja confianza.

**Comandos:**

#### Listar revisiones pendientes
```bash
python -m intelligence_capture.ocr.ocr_reviewer_cli list-pending \
  --status pending_review \
  --priority high \
  --limit 20
```

**Opciones:**
- `--status`: Filtrar por estado (pending_review, in_review, approved, rejected)
- `--priority`: Filtrar por prioridad (high, normal, low)
- `--segment-type`: Filtrar por tipo (handwriting, printed_degraded, tables, mixed)
- `--limit`: Número de items a mostrar

#### Revisar segmento específico
```bash
python -m intelligence_capture.ocr.ocr_reviewer_cli review 123 \
  --reviewer patricia@comversa.com
```

**Flujo de revisión:**
1. Mostrar información del segmento (documento, página, confianza, tipo)
2. Mostrar texto OCR original
3. Referencia a imagen recortada para revisión visual
4. Opciones:
   - Aprobar con correcciones
   - Rechazar (ilegible)
   - Saltar (revisar después)
   - Cancelar

#### Estadísticas de revisión
```bash
python -m intelligence_capture.ocr.ocr_reviewer_cli stats \
  --reviewer patricia@comversa.com \
  --days 30
```

Muestra:
- Total de revisiones
- Pendientes/Aprobadas/Rechazadas
- Confianza promedio
- Métricas por revisor (tasa de aprobación, tiempo promedio)

#### Exportar revisiones
```bash
python -m intelligence_capture.ocr.ocr_reviewer_cli export \
  --status approved \
  --output revisiones_aprobadas.json
```

Exporta datos de revisión a JSON para análisis o entrenamiento de modelos.

---

## Integración con Sistema RAG 2.0

### Flujo de Procesamiento

```
Documento PDF/Imagen
    ↓
DocumentProcessor (Task 3)
    ↓
OCRCoordinator.process_document()
    ↓
    ├─→ MistralPixtralClient (primario)
    │   ├─→ Confianza alta (>0.90 impreso, >0.70 manuscrito)
    │   │       ↓
    │   │   Chunking (Task 5)
    │   │
    │   └─→ Confianza baja
    │           ↓
    │       ocr_review_queue (PostgreSQL)
    │
    └─→ Tesseract (fallback si Mistral falla)
            ↓
        Similar al flujo Mistral
```

### Rate Limiting

El OCRCoordinator utiliza el rate limiter compartido (`intelligence_capture.rate_limiter`) con:
- **Límite:** 5 llamadas OCR por minuto
- **Compartido con:** Pipeline de extracción de entidades
- **Propósito:** Prevenir throttling de API

### Cola de Revisión Manual

**Tabla:** `ocr_review_queue` (PostgreSQL)

**Campos principales:**
- `document_id`: UUID del documento
- `page_number`: Número de página
- `segment_index`: Índice de segmento en página
- `ocr_text`: Texto OCR original
- `confidence`: Puntuación de confianza (0.0-1.0)
- `ocr_engine`: Motor usado (mistral_pixtral, tesseract)
- `status`: Estado del flujo (pending_review, in_review, approved, rejected, skipped)
- `corrected_text`: Texto corregido manualmente
- `reviewed_by`: Revisor asignado
- `priority`: Prioridad (high, normal, low) - auto-asignada por confianza

**Triggers automáticos:**
- `set_ocr_review_priority()`: Auto-asigna prioridad basada en confianza
- `generate_ocr_crop_path()`: Auto-genera ruta de recorte de imagen

**Vistas útiles:**
- `ocr_high_priority_queue`: Revisiones de alta prioridad ordenadas por confianza
- `ocr_reviewer_stats`: Métricas de desempeño de revisores

---

## Configuración

### Variables de Entorno

```bash
# Mistral API (requerido para MistralPixtralClient)
export MISTRAL_API_KEY="tu-api-key-aqui"

# PostgreSQL (requerido para OCRCoordinator y CLI)
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

### Instalación de Dependencias

```bash
# Python packages
pip install -r requirements-rag2.txt

# Tesseract (macOS)
brew install tesseract tesseract-lang

# Tesseract (Ubuntu)
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# Verificar instalación
tesseract --version
tesseract --list-langs  # Debe incluir 'spa'

# Modelo spaCy español (para Task 5: Chunking)
python -m spacy download es_core_news_md
```

### Migración de Base de Datos

```bash
# Aplicar esquema ocr_review_queue
psql $DATABASE_URL -f scripts/migrations/2025_01_02_ocr_review_queue.sql
```

---

## Testing

### Unit Tests

```bash
# Ejecutar todos los tests OCR
pytest tests/test_ocr_client.py -v

# Con cobertura
pytest tests/test_ocr_client.py --cov=intelligence_capture.ocr --cov-report=html

# Test específico
pytest tests/test_ocr_client.py::TestMistralPixtralClient::test_extract_text_success -v
```

### Tests de Integración

```bash
# Crear imágenes de prueba
mkdir -p data/test_images

# Test Mistral Pixtral (requiere MISTRAL_API_KEY)
python -c "
from intelligence_capture.ocr import MistralPixtralClient
from pathlib import Path

client = MistralPixtralClient()
result = client.extract_text(
    Path('data/test_images/sample_handwritten.jpg'),
    document_type='handwritten'
)
print(f'Texto: {result[\"text\"][:100]}...')
print(f'Confianza: {result[\"confidence\"]:.2f}')
"

# Test Tesseract
python -c "
from intelligence_capture.ocr import TesseractFallback
from pathlib import Path

client = TesseractFallback()
result = client.extract_text(Path('data/test_images/sample_printed.png'))
print(f'Texto: {result[\"text\"][:100]}...')
print(f'Confianza: {result[\"confidence\"]:.2f}')
"
```

---

## Troubleshooting

### Error: "MISTRAL_API_KEY no configurado"
**Solución:**
```bash
export MISTRAL_API_KEY="tu-api-key"
```

### Error: "Tesseract no está instalado"
**Solución:**
```bash
# macOS
brew install tesseract tesseract-lang

# Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

### Error: Tesseract no encuentra idioma español
**Solución:**
```bash
# Verificar idiomas instalados
tesseract --list-langs

# Instalar paquete de idioma español
# macOS
brew reinstall tesseract-lang

# Ubuntu
sudo apt-get install tesseract-ocr-spa
```

### CLI no se conecta a PostgreSQL
**Solución:**
1. Verificar `DATABASE_URL` configurado
2. Verificar que migración `2025_01_02_ocr_review_queue.sql` se aplicó
3. Implementar integración async en `ocr_reviewer_cli.py` (actualmente usa datos de ejemplo)

### Confianza muy baja en todos los documentos
**Causas posibles:**
- Calidad de imagen muy baja (resolver: mejorar escaneo)
- Tipo de documento incorrecto (resolver: ajustar `document_type`)
- Idioma incorrecto (resolver: verificar `language='es'`)

---

## Roadmap

### Próximos Pasos (Task 4 - Pendiente)

- [ ] Completar integración PostgreSQL async en `OCRCoordinator._enqueue_for_review()`
- [ ] Conectar comandos CLI a base de datos PostgreSQL de producción
- [ ] Crear imágenes de prueba para testing de integración
- [ ] Wire OCR coordinator en DocumentProcessor (Task 3)

### Mejoras Futuras

- [ ] Soporte de bounding boxes estructuradas de Mistral Pixtral
- [ ] Caché de resultados OCR para evitar reprocesamiento
- [ ] Métricas de calidad OCR por tipo de documento
- [ ] Entrenamiento de modelo de confianza personalizado
- [ ] Interfaz web para revisión manual (alternativa a CLI)
- [ ] Exportación de datos de entrenamiento para fine-tuning
- [ ] Soporte de OCR multi-idioma (inglés, portugués)

---

## Referencias

- **Mistral API Docs:** https://docs.mistral.ai/
- **Tesseract OCR:** https://github.com/tesseract-ocr/tesseract
- **Click CLI Framework:** https://click.palletsprojects.com/
- **Task 4 Spec:** `.kiro/specs/rag-2.0-enhancement/tasks.md` (líneas 46-53)
- **Schema Migration:** `scripts/migrations/2025_01_02_ocr_review_queue.sql`
- **Coding Standards:** `.ai/CODING_STANDARDS.md`

---

**Última actualización:** 2025-11-09
**Versión:** 1.0.0
**Autor:** intake_processing agent
