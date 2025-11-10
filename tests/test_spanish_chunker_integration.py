"""
Integration tests para Spanish-Aware Chunking con fixtures reales

Tests de integración con:
- Documentos en español reales
- Múltiples formatos (transcripciones, reportes, procedimientos)
- Validación de chunking end-to-end
"""

import pytest
from pathlib import Path
from intelligence_capture.chunking import SpanishChunker
from intelligence_capture.models.document_payload import DocumentPayload


class TestSpanishChunkerIntegration:
    """Tests de integración con documentos en español"""

    @pytest.fixture
    def chunker(self):
        """Crear chunker"""
        try:
            return SpanishChunker()
        except ValueError as e:
            pytest.skip(f"spaCy modelo español no instalado: {e}")

    @pytest.fixture
    def interview_transcript(self):
        """Fixture: transcripción de entrevista real"""
        content = """
Entrevista con Jefe de Finanzas - Los Tajibos

Problema Principal: Reconciliación Manual de Facturas

La reconciliación de facturas es uno de los procesos más críticos y problemáticos
en nuestro departamento. Actualmente, todo el proceso se realiza de forma manual,
lo que consume aproximadamente tres horas diarias del equipo de contabilidad.

El proceso actual involucra los siguientes pasos:

1. Recepción de Facturas
El proveedor envía la factura por correo electrónico o físicamente. Muchas veces
llegan en diferentes formatos (PDF, imagen escaneada, papel) lo que dificulta
su procesamiento.

2. Validación Manual
El contador debe abrir cada factura individualmente y verificar:
- Que los datos del proveedor sean correctos
- Que los montos coincidan con la orden de compra
- Que los productos o servicios listados correspondan
- Que la fecha de emisión sea válida

3. Búsqueda en el Sistema
Una vez validada la factura, hay que buscar la orden de compra correspondiente
en el sistema ERP. Esto puede tomar varios minutos porque el sistema es lento
y muchas veces hay que buscar por diferentes criterios.

4. Comparación y Conciliación
Se comparan los datos de la factura con:
- La orden de compra original
- El registro de recepción de mercadería
- El contrato con el proveedor (si existe)

Cualquier discrepancia requiere comunicación con el proveedor o con el
departamento de compras, lo que puede demorar días.

5. Registro en Hojas de Cálculo
Como el sistema ERP no tiene todas las funcionalidades necesarias, mantenemos
hojas de cálculo de Excel paralelas donde registramos:
- Estado de cada factura
- Observaciones y pendientes
- Fechas de seguimiento
- Responsables de cada caso

6. Aprobación y Pago
Una vez conciliada la factura, se envía para aprobación del jefe de departamento
y luego se programa el pago según las condiciones acordadas con el proveedor.

Impacto del Problema:

El impacto de este proceso manual es significativo:

- Tiempo: Tres horas diarias del equipo, que podría dedicarse a análisis
  más estratégicos como proyecciones financieras o análisis de costos.

- Errores: Aproximadamente 5-7% de las facturas tienen errores en el registro
  manual, lo que genera reclamos de proveedores y problemas de caja.

- Retrasos: El proceso manual causa que el cierre mensual se retrase 2-3 días,
  afectando la presentación oportuna de reportes financieros a gerencia.

- Costos: Los errores y retrasos generan costos adicionales en términos de
  multas por pagos tardíos y relaciones deterioradas con proveedores.

- Auditoría: Durante auditorías, es muy difícil rastrear el historial completo
  de una factura porque la información está dispersa entre el ERP, correos
  electrónicos y hojas de cálculo.

Solución Propuesta:

Lo ideal sería tener un sistema que:

1. Reciba facturas automáticamente por correo electrónico o portal web
2. Extraiga los datos de la factura automáticamente (OCR si es imagen)
3. Busque la orden de compra correspondiente automáticamente
4. Compare los datos y marque discrepancias para revisión humana
5. Envíe notificaciones automáticas cuando se requiera acción
6. Mantenga un registro de auditoría completo en el sistema

Esto reduciría el tiempo de reconciliación en al menos un 70% y mejoraría
significativamente la precisión del proceso.

Otros Procesos Relacionados:

Este problema está conectado con otros procesos problemáticos:

- Gestión de Órdenes de Compra: Muchas veces las órdenes de compra no están
  bien registradas en el sistema, lo que dificulta la reconciliación.

- Comunicación con Proveedores: No tenemos un canal estandarizado de
  comunicación, lo que genera confusión y retrasos.

- Reportes Financieros: La demora en la reconciliación afecta la calidad
  y oportunidad de los reportes mensuales.

Presupuesto y Recursos:

Para implementar una solución de automatización, estimamos que se necesitaría:

- Inversión inicial: $15,000 - $20,000 USD para software y implementación
- Capacitación: 2 semanas para el equipo de finanzas
- Tiempo de implementación: 3-4 meses
- ROI esperado: Recuperación de la inversión en 12-15 meses

El retorno vendría principalmente de:
- Reducción de tiempo del personal (70% de 3 horas diarias)
- Reducción de errores (ahorro en multas y reclamos)
- Mejor gestión de flujo de caja
- Cierre mensual más rápido y preciso

Conclusión:

La reconciliación manual de facturas es uno de nuestros principales cuellos
de botella. Una solución de automatización tendría un impacto significativo
en la eficiencia del departamento y la calidad de nuestra información financiera.
"""
        return content

    @pytest.fixture
    def procedure_document(self):
        """Fixture: documento de procedimiento con estructura"""
        content = """
# Procedimiento: Recepción de Huéspedes

## 1. Objetivo

Establecer el proceso estándar para la recepción de huéspedes en el Hotel Los Tajibos,
asegurando una experiencia de servicio de calidad y cumplimiento de normativas.

## 2. Alcance

Este procedimiento aplica a todo el personal de recepción, incluyendo:
- Recepcionistas de turno
- Supervisores de front desk
- Personal de conserjería
- Gerente de operaciones

## 3. Responsabilidades

| Rol | Responsabilidad |
|-----|-----------------|
| Recepcionista | Ejecutar el proceso de check-in según este procedimiento |
| Supervisor | Supervisar cumplimiento y resolver excepciones |
| Gerente | Auditar cumplimiento y actualizar procedimiento |

## 4. Proceso de Check-In

### 4.1 Preparación

Antes de la llegada del huésped:

1. Revisar lista de llegadas del día en el sistema PMS
2. Verificar disponibilidad de habitaciones
3. Preparar llaves de habitación
4. Coordinar con housekeeping estado de habitaciones

### 4.2 Recepción del Huésped

Cuando el huésped llega:

1. Saludar con cortesía: "Buenos días/tardes, bienvenido a Hotel Los Tajibos"
2. Solicitar documento de identidad y reserva
3. Verificar reserva en el sistema PMS

### 4.3 Registro

Proceso de registro en sistema:

1. Ingresar datos del huésped:
   - Nombre completo
   - Documento de identidad
   - País de origen
   - Fecha de nacimiento
   - Contacto (email y teléfono)

2. Confirmar detalles de la reserva:
   - Tipo de habitación
   - Fecha de entrada y salida
   - Número de personas
   - Régimen alimenticio

3. Solicitar firma del registro de huéspedes
4. Procesar garantía de pago (tarjeta de crédito o depósito)

### 4.4 Información al Huésped

Proporcionar al huésped:

- Horarios de desayuno y restaurantes
- Servicios disponibles (spa, piscina, gimnasio)
- Información de seguridad y emergencias
- Normas del hotel

### 4.5 Asignación de Habitación

1. Entregar llave de habitación
2. Indicar ubicación de habitación en plano
3. Ofrecer acompañamiento del botones
4. Desear buena estadía

## 5. Excepciones

### 5.1 Reserva No Encontrada

Si no se encuentra la reserva:

1. Verificar en diferentes fuentes (email, OTAs)
2. Contactar con el departamento de reservas
3. Si persiste problema, escalar a supervisor
4. Ofrecer solución alternativa al huésped

### 5.2 Sobreventa

En caso de sobreventa de habitaciones:

1. Informar inmediatamente a supervisor
2. Contactar con hotel alternativo de categoría similar
3. Ofrecer compensación según política de la empresa
4. Gestionar transporte del huésped

### 5.3 Problemas con Pago

Si hay problemas con el medio de pago:

1. Explicar políticas de pago al huésped
2. Ofrecer alternativas de pago
3. Si no se resuelve, escalar a supervisor
4. No entregar habitación sin garantía de pago confirmada

## 6. Indicadores de Desempeño

El proceso se mide con los siguientes KPIs:

- Tiempo promedio de check-in: < 5 minutos
- Satisfacción del huésped: > 4.5/5
- Errores en registro: < 2%
- Quejas por proceso de check-in: < 1%

## 7. Registros y Documentación

Documentos generados en el proceso:

1. Registro de huésped (físico y digital)
2. Voucher de garantía de pago
3. Encuesta de satisfacción (opcional)
4. Reporte de excepciones (si aplica)

Estos documentos se archivan según política de retención:
- Físicos: 1 año
- Digitales: 3 años

## 8. Actualizaciones

Este procedimiento se revisa:
- Anualmente por el Gerente de Operaciones
- Cuando haya cambios en sistemas o normativas
- Cuando análisis de KPIs indique necesidad de mejora

Última actualización: 15 de Octubre, 2024
Próxima revisión: 15 de Octubre, 2025

## 9. Anexos

### Anexo A: Lista de Verificación Check-In

```
[ ] Saludar al huésped
[ ] Solicitar identificación
[ ] Verificar reserva en PMS
[ ] Registrar datos del huésped
[ ] Confirmar detalles de reserva
[ ] Procesar garantía de pago
[ ] Entregar información del hotel
[ ] Asignar habitación
[ ] Entregar llave
[ ] Desear buena estadía
```

### Anexo B: Frases Estándar de Servicio

Utilizar las siguientes frases para mantener calidad de servicio:

- "Es un placer recibirle en Hotel Los Tajibos"
- "¿En qué puedo asistirle?"
- "Permítame verificar su reserva"
- "Todo está listo para su estadía"
- "Que disfrute su estancia con nosotros"
"""
        return content

    def test_interview_chunking(self, chunker, interview_transcript):
        """Test chunking de transcripción de entrevista"""
        payload = DocumentPayload(
            document_id="interview-001",
            org_id="los_tajibos",
            checksum="abc123",
            source_type="interview",
            source_format="txt",
            mime_type="text/plain",
            original_path=Path("/tmp/interview.txt"),
            content=interview_transcript,
            language="es",
            page_count=1
        )

        chunks = chunker.chunk_document(payload)

        # Verificar que se generaron múltiples chunks
        assert len(chunks) > 3  # Contenido largo debería generar varios chunks

        # Verificar que cada chunk está en español
        for chunk in chunks:
            # Verificar características del español
            spanish_features = chunk['metadata']['spanish_features']
            assert spanish_features['has_accents'] is True
            assert spanish_features['stopword_ratio'] > 0.2  # Texto español tiene stopwords

        # Verificar que se preservó contenido
        all_content = ' '.join([c['content'] for c in chunks])
        assert "reconciliación" in all_content.lower()
        assert "facturas" in all_content.lower()
        assert "manual" in all_content.lower()

    def test_procedure_markdown_chunking(self, chunker, procedure_document):
        """Test chunking de procedimiento con Markdown"""
        payload = DocumentPayload(
            document_id="procedure-001",
            org_id="los_tajibos",
            checksum="def456",
            source_type="sharepoint",
            source_format="md",
            mime_type="text/markdown",
            original_path=Path("/tmp/procedure.md"),
            content=procedure_document,
            language="es",
            page_count=1
        )

        # Usar chunking con preservación de Markdown
        chunks = chunker.chunk_with_markdown_preservation(payload)

        # Verificar que se generaron chunks
        assert len(chunks) > 0

        # Verificar que se preservaron encabezados
        heading_chunks = [c for c in chunks if '##' in c['content']]
        assert len(heading_chunks) > 0

        # Verificar detección de tabla
        table_chunks = [c for c in chunks if c['metadata']['contains_table']]
        assert len(table_chunks) > 0  # El documento tiene tabla de responsabilidades

        # Verificar detección de lista
        list_chunks = [c for c in chunks if c['metadata']['contains_list']]
        assert len(list_chunks) > 0  # El documento tiene múltiples listas

        # Verificar detección de código
        code_chunks = [c for c in chunks if c['metadata']['contains_code']]
        assert len(code_chunks) > 0  # El documento tiene bloque de código (checklist)

    def test_chunk_continuity(self, chunker, interview_transcript):
        """Verificar continuidad entre chunks consecutivos"""
        payload = DocumentPayload(
            document_id="continuity-test",
            org_id="test_org",
            checksum="ghi789",
            source_type="email",
            source_format="txt",
            mime_type="text/plain",
            original_path=Path("/tmp/continuity.txt"),
            content=interview_transcript,
            language="es",
            page_count=1
        )

        chunks = chunker.chunk_document(payload)

        # Verificar que los offsets son continuos (con superposición)
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]['metadata']
            next_chunk = chunks[i + 1]['metadata']

            current_end = current_chunk['span_offsets'][1]
            next_start = next_chunk['span_offsets'][0]

            # El siguiente chunk debería empezar antes del fin del actual
            # (superposición de ~50 tokens)
            assert next_start < current_end

    def test_metadata_accuracy(self, chunker, procedure_document):
        """Verificar precisión de metadatos"""
        payload = DocumentPayload(
            document_id="metadata-test",
            org_id="los_tajibos",
            checksum="jkl012",
            source_type="sharepoint",
            source_format="md",
            mime_type="text/markdown",
            original_path=Path("/tmp/metadata.md"),
            content=procedure_document,
            language="es",
            page_count=1,
            sections=[
                {"title": "Procedimiento: Recepción de Huéspedes", "level": 1, "page": 1}
            ]
        )

        chunks = chunker.chunk_document(payload)

        for chunk in chunks:
            metadata = chunk['metadata']

            # Verificar metadatos básicos
            assert metadata['document_id'] == "metadata-test"
            assert metadata['token_count'] > 0
            assert metadata['char_count'] > 0
            assert len(metadata['span_offsets']) == 2

            # Verificar que el contenido coincide con los offsets
            content_length = len(chunk['content'])
            offset_length = metadata['span_offsets'][1] - metadata['span_offsets'][0]

            # Los offsets deberían corresponder aproximadamente con el contenido
            # (puede haber diferencias por espacios en blanco)
            assert abs(content_length - offset_length) < content_length * 0.1

    def test_spanish_stopword_filtering(self, chunker):
        """Verificar que las características del español se calculan correctamente"""
        # Texto con alta densidad de stopwords
        stopword_heavy = """
        el de la que y a en un por con su para como estar
        tener le lo todo pero más hacer o poder decir este
        """

        # Texto con baja densidad de stopwords (nombres propios, términos técnicos)
        technical_text = """
        PostgreSQL implementación índice HNSW vectorización
        embedding chunk tokenización stemming algoritmo
        """

        for content in [stopword_heavy, technical_text]:
            payload = DocumentPayload(
                document_id="stopword-test",
                org_id="test_org",
                checksum="mno345",
                source_type="test",
                source_format="txt",
                mime_type="text/plain",
                original_path=Path("/tmp/test.txt"),
                content=content,
                language="es",
                page_count=1
            )

            chunks = chunker.chunk_document(payload)

            if chunks:
                features = chunks[0]['metadata']['spanish_features']

                # El texto con stopwords debería tener ratio alto
                if content == stopword_heavy:
                    assert features['stopword_ratio'] > 0.7

                # El texto técnico debería tener ratio bajo
                if content == technical_text:
                    assert features['stopword_ratio'] < 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
