#!/usr/bin/env python3
"""
OCR Review CLI - Manual review of low-confidence OCR segments
Workflow: pending_review → in_review → approved/rejected/skipped
"""

import click
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from tabulate import tabulate
import json

# Agregar path de proyecto para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Placeholder para conexión Postgres (completar en integración)
# from intelligence_capture.database import get_postgres_connection


@click.group()
def cli():
    """
    OCR Review CLI - Revisión manual de segmentos OCR de baja confianza

    Comandos disponibles:
        list-pending    Listar revisiones pendientes
        review          Revisar segmento específico
        stats           Mostrar estadísticas de revisión
        export          Exportar datos de revisión
    """
    pass


@cli.command()
@click.option('--status', default='pending_review', help='Filtrar por estado (pending_review, in_review, approved, rejected)')
@click.option('--limit', default=10, help='Número de items a mostrar')
@click.option('--priority', default=None, help='Filtrar por prioridad (high, normal, low)')
@click.option('--segment-type', default=None, help='Filtrar por tipo (handwriting, printed_degraded, tables, mixed)')
def list_pending(status: str, limit: int, priority: Optional[str], segment_type: Optional[str]):
    """Listar revisiones pendientes de OCR"""

    click.echo(f"\n{'='*80}")
    click.echo(f"📋 Cola de Revisión OCR - Estado: {status}")
    click.echo(f"{'='*80}\n")

    try:
        # Conectar a PostgreSQL
        # conn = get_postgres_connection()

        # Construir query
        query = """
        SELECT
            id,
            document_id,
            page_number,
            segment_index,
            SUBSTRING(ocr_text, 1, 60) as preview,
            confidence,
            ocr_engine,
            priority,
            segment_type,
            created_at,
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at)) / 3600 AS age_hours
        FROM ocr_review_queue
        WHERE status = $1
        """

        params = [status]

        if priority:
            query += " AND priority = $2"
            params.append(priority)

        if segment_type:
            query += f" AND segment_type = ${len(params) + 1}"
            params.append(segment_type)

        query += " ORDER BY priority DESC, confidence ASC, created_at ASC"
        query += f" LIMIT ${len(params) + 1}"
        params.append(limit)

        # Ejecutar query (simulado por ahora)
        # rows = await conn.fetch(query, *params)

        # Datos de ejemplo para demostración
        rows = [
            {
                'id': 1,
                'document_id': '550e8400-e29b-41d4-a716-446655440000',
                'page_number': 3,
                'segment_index': 2,
                'preview': 'Rconclición mnual d factura causa rtrasos en...',
                'confidence': 0.45,
                'ocr_engine': 'mistral_pixtral',
                'priority': 'high',
                'segment_type': 'handwriting',
                'created_at': datetime.now(),
                'age_hours': 2.5
            },
            {
                'id': 2,
                'document_id': '550e8400-e29b-41d4-a716-446655440001',
                'page_number': 1,
                'segment_index': 0,
                'preview': 'El proceimiento de compra reqiere aprobción...',
                'confidence': 0.67,
                'ocr_engine': 'tesseract',
                'priority': 'normal',
                'segment_type': 'printed_degraded',
                'created_at': datetime.now(),
                'age_hours': 1.2
            }
        ]

        if not rows:
            click.echo("  ℹ️  No hay revisiones pendientes con los filtros especificados.\n")
            return

        # Formatear tabla
        table_data = []
        for row in rows:
            table_data.append([
                row['id'],
                f"{row['page_number']}/{row['segment_index']}",
                row['preview'] + '...',
                f"{row['confidence']:.2f}",
                row['ocr_engine'],
                row['priority'],
                row['segment_type'],
                f"{row['age_hours']:.1f}h"
            ])

        headers = ['ID', 'Pág/Seg', 'Preview OCR', 'Conf.', 'Motor', 'Prioridad', 'Tipo', 'Edad']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

        click.echo(f"\n  Total: {len(rows)} items")
        click.echo(f"  Para revisar: ocr-review review <ID>\n")

    except Exception as e:
        click.echo(f"\n❌ Error listando revisiones: {e}\n", err=True)
        sys.exit(1)


@cli.command()
@click.argument('review_id', type=int)
@click.option('--reviewer', default=None, help='Nombre del revisor (default: $USER)')
def review(review_id: int, reviewer: Optional[str]):
    """Revisar segmento OCR específico"""

    if reviewer is None:
        reviewer = os.getenv('USER', 'reviewer')

    click.echo(f"\n{'='*80}")
    click.echo(f"🔍 Revisión OCR - ID: {review_id}")
    click.echo(f"   Revisor: {reviewer}")
    click.echo(f"{'='*80}\n")

    try:
        # Obtener segmento de base de datos
        # conn = get_postgres_connection()
        # row = await conn.fetchrow(
        #     "SELECT * FROM ocr_review_queue WHERE id = $1",
        #     review_id
        # )

        # Datos de ejemplo
        row = {
            'id': review_id,
            'document_id': '550e8400-e29b-41d4-a716-446655440000',
            'page_number': 3,
            'segment_index': 2,
            'ocr_text': 'Rconclición mnual d factura causa rtrasos en el proceimiento',
            'confidence': 0.45,
            'ocr_engine': 'mistral_pixtral',
            'priority': 'high',
            'segment_type': 'handwriting',
            'image_crop_url': 'data/ocr_crops/550e8400.../page_3_segment_2.png',
            'metadata': {'language_detected': 'es'}
        }

        if not row:
            click.echo(f"❌ Error: Revisión ID {review_id} no encontrada.\n", err=True)
            sys.exit(1)

        # Mostrar información del segmento
        click.echo("📄 Información del Segmento:")
        click.echo(f"   Documento: {row['document_id']}")
        click.echo(f"   Página/Segmento: {row['page_number']}/{row['segment_index']}")
        click.echo(f"   Motor OCR: {row['ocr_engine']}")
        click.echo(f"   Confianza: {row['confidence']:.2f}")
        click.echo(f"   Tipo: {row['segment_type']}")
        click.echo(f"   Prioridad: {row['priority']}\n")

        click.echo("📝 Texto OCR Original:")
        click.echo(f"   {row['ocr_text']}\n")

        click.echo(f"🖼️  Imagen: {row['image_crop_url']}")
        click.echo("   (Abrir imagen manualmente para revisar)\n")

        # Prompt de acción
        click.echo("Acciones disponibles:")
        click.echo("  1. Aprobar con correcciones")
        click.echo("  2. Rechazar (ilegible)")
        click.echo("  3. Saltar (revisar después)")
        click.echo("  4. Cancelar\n")

        action = click.prompt("Seleccionar acción", type=int)

        if action == 1:
            # Aprobar con texto corregido
            corrected_text = click.prompt(
                "Texto corregido",
                default=row['ocr_text']
            )
            review_notes = click.prompt(
                "Notas de revisión (opcional)",
                default="",
                show_default=False
            )

            # Actualizar base de datos
            # await conn.execute("""
            #     UPDATE ocr_review_queue
            #     SET status = 'approved',
            #         corrected_text = $1,
            #         reviewed_by = $2,
            #         reviewed_at = CURRENT_TIMESTAMP,
            #         review_notes = $3
            #     WHERE id = $4
            # """, corrected_text, reviewer, review_notes, review_id)

            click.echo(f"\n✅ Revisión ID {review_id} aprobada y guardada.\n")

        elif action == 2:
            # Rechazar
            review_notes = click.prompt(
                "Motivo de rechazo",
                default="Texto ilegible incluso para revisión manual"
            )

            # await conn.execute("""
            #     UPDATE ocr_review_queue
            #     SET status = 'rejected',
            #         reviewed_by = $1,
            #         reviewed_at = CURRENT_TIMESTAMP,
            #         review_notes = $2
            #     WHERE id = $3
            # """, reviewer, review_notes, review_id)

            click.echo(f"\n✅ Revisión ID {review_id} rechazada.\n")

        elif action == 3:
            # Saltar
            click.echo(f"\n⏭️  Revisión ID {review_id} saltada (permanece pending_review).\n")

        else:
            click.echo("\n❌ Revisión cancelada.\n")

    except Exception as e:
        click.echo(f"\n❌ Error en revisión: {e}\n", err=True)
        sys.exit(1)


@cli.command()
@click.option('--reviewer', default=None, help='Filtrar por revisor')
@click.option('--days', default=7, help='Días atrás para estadísticas')
def stats(reviewer: Optional[str], days: int):
    """Mostrar estadísticas de revisión OCR"""

    click.echo(f"\n{'='*80}")
    click.echo(f"📊 Estadísticas de Revisión OCR - Últimos {days} días")
    if reviewer:
        click.echo(f"   Revisor: {reviewer}")
    click.echo(f"{'='*80}\n")

    try:
        # Query estadísticas de base de datos
        # conn = get_postgres_connection()

        # Estadísticas generales
        # total_stats = await conn.fetchrow("""
        #     SELECT
        #         COUNT(*) as total_reviews,
        #         COUNT(*) FILTER (WHERE status = 'pending_review') as pending,
        #         COUNT(*) FILTER (WHERE status = 'approved') as approved,
        #         COUNT(*) FILTER (WHERE status = 'rejected') as rejected,
        #         AVG(confidence) as avg_confidence
        #     FROM ocr_review_queue
        #     WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '{days} days'
        # """)

        # Datos de ejemplo
        total_stats = {
            'total_reviews': 45,
            'pending': 12,
            'approved': 28,
            'rejected': 5,
            'avg_confidence': 0.62
        }

        click.echo("🔢 Resumen General:")
        click.echo(f"   Total revisiones: {total_stats['total_reviews']}")
        click.echo(f"   Pendientes: {total_stats['pending']}")
        click.echo(f"   Aprobadas: {total_stats['approved']}")
        click.echo(f"   Rechazadas: {total_stats['rejected']}")
        click.echo(f"   Confianza promedio: {total_stats['avg_confidence']:.2f}\n")

        # Estadísticas por revisor
        click.echo("👥 Revisores:")

        reviewer_stats = [
            {'reviewed_by': 'patricia@comversa.com', 'total_reviews': 18, 'approved_count': 15, 'avg_review_time_minutes': 3.2},
            {'reviewed_by': 'samuel@comversa.com', 'total_reviews': 10, 'approved_count': 8, 'avg_review_time_minutes': 4.1}
        ]

        table_data = []
        for r in reviewer_stats:
            approval_rate = (r['approved_count'] / r['total_reviews'] * 100) if r['total_reviews'] > 0 else 0
            table_data.append([
                r['reviewed_by'],
                r['total_reviews'],
                r['approved_count'],
                f"{approval_rate:.1f}%",
                f"{r['avg_review_time_minutes']:.1f} min"
            ])

        headers = ['Revisor', 'Total', 'Aprobadas', 'Tasa Aprobación', 'Tiempo Promedio']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        click.echo()

    except Exception as e:
        click.echo(f"\n❌ Error obteniendo estadísticas: {e}\n", err=True)
        sys.exit(1)


@cli.command()
@click.option('--output', default='ocr_review_export.json', help='Archivo de salida')
@click.option('--status', default='approved', help='Estado a exportar')
def export(output: str, status: str):
    """Exportar datos de revisión a JSON"""

    click.echo(f"\n📤 Exportando revisiones con estado '{status}' a {output}...\n")

    try:
        # conn = get_postgres_connection()
        # rows = await conn.fetch("""
        #     SELECT
        #         document_id, page_number, segment_index,
        #         ocr_text, corrected_text, confidence,
        #         reviewed_by, review_notes, reviewed_at
        #     FROM ocr_review_queue
        #     WHERE status = $1
        #     ORDER BY reviewed_at DESC
        # """, status)

        # Datos de ejemplo
        rows = [
            {
                'document_id': '550e8400-e29b-41d4-a716-446655440000',
                'page_number': 3,
                'segment_index': 2,
                'ocr_text': 'Rconclición mnual',
                'corrected_text': 'Reconciliación manual',
                'confidence': 0.45,
                'reviewed_by': 'patricia@comversa.com',
                'review_notes': 'Corregido',
                'reviewed_at': datetime.now().isoformat()
            }
        ]

        # Convertir a JSON serializable
        export_data = []
        for row in rows:
            export_data.append(dict(row))

        # Guardar archivo
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        click.echo(f"✅ Exportadas {len(export_data)} revisiones a {output}\n")

    except Exception as e:
        click.echo(f"\n❌ Error exportando: {e}\n", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
