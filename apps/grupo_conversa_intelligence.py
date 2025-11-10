"""
Streamlit app for exploring Grupo Conversa intelligence assets.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st
from anthropic import Anthropic
from anthropic._types import NOT_GIVEN
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------------------------------------------------------------------------
# App configuration & constants
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Grupo Conversa Intelligence", layout="wide")

DEFAULT_DB_PATH = os.environ.get("INTELLIGENCE_DB_PATH", "data/full_intelligence.db")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

ENTITY_TABLES: Dict[str, str] = {
    "processes": "Procesos",
    "pain_points": "Puntos de dolor",
    "automation_candidates": "Oportunidades de automatización",
    "interviews": "Entrevistas",
}


# ---------------------------------------------------------------------------
# Helpers: database and caching
# ---------------------------------------------------------------------------

def list_available_databases(data_dir: str = "data") -> List[Path]:
    """Return every .db file under data/ for quick selection."""
    dir_path = Path(data_dir)
    if not dir_path.exists():
        return []
    return sorted(dir_path.glob("*.db"))


@st.cache_resource(show_spinner=False)
def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Return cached SQLite connection (WAL-friendly)."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_data(show_spinner=False)
def fetch_table(db_path: str, table_name: str) -> pd.DataFrame:
    """Read a table into a DataFrame; return empty if it does not exist."""
    conn = get_db_connection(db_path)
    try:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    except sqlite3.OperationalError:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def fetch_count(db_path: str, table_name: str) -> int:
    """Count rows in table; return 0 when table is missing."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        value = cursor.fetchone()
        return int(value[0]) if value else 0
    except sqlite3.OperationalError:
        return 0


# ---------------------------------------------------------------------------
# Helpers: Anthropic client & prompt utilities
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_anthropic_client() -> Optional[Anthropic]:
    """Build Anthropic client if API key is present."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def call_claude(prompt: str, max_tokens: int = 2000) -> str:
    """Invoke Anthropic Messages API with Spanish prompt."""
    client = get_anthropic_client()
    if not client:
        raise RuntimeError("Configura ANTHROPIC_API_KEY antes de usar los agentes.")

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}],
        metadata=NOT_GIVEN,
    )
    return response.content[0].text.strip()


def format_process_for_prompt(process_row: pd.Series) -> str:
    """Pretty string for process context in prompts."""
    fields = {
        "Empresa": process_row.get("company"),
        "Nombre del proceso": process_row.get("name"),
        "Propietario": process_row.get("owner"),
        "Dominio": process_row.get("domain"),
        "Descripción": process_row.get("description"),
        "Entradas": process_row.get("inputs"),
        "Salidas": process_row.get("outputs"),
        "Sistemas": process_row.get("systems"),
        "Frecuencia": process_row.get("frequency"),
        "Dependencias": process_row.get("dependencies"),
    }
    lines = [f"- {label}: {value}" for label, value in fields.items() if value]
    return "\n".join(lines) if lines else "Sin información adicional."


def summarize_pain_points(df: pd.DataFrame, limit: int = 6) -> str:
    """Return Spanish summary of key pain points."""
    if df.empty:
        return "Sin puntos de dolor disponibles."

    subset = df.head(limit)
    rows = []
    for _, row in subset.iterrows():
        desc = row.get("description") or "Sin descripción"
        severity = row.get("severity") or "sin severidad"
        frequency = row.get("frequency") or "sin frecuencia"
        impact = row.get("impact_description") or row.get("type") or ""
        rows.append(
            f"- {row.get('company', 'Empresa desconocida')}: {desc} "
            f"(Severidad: {severity}, Frecuencia: {frequency}, Impacto: {impact})"
        )
    return "\n".join(rows)


def summarize_automations(df: pd.DataFrame, limit: int = 5) -> str:
    """Return high-level summary of automation candidates."""
    if df.empty:
        return "Sin oportunidades de automatización registradas."

    subset = df.head(limit)
    rows = []
    for _, row in subset.iterrows():
        name = row.get("name") or "Caso sin nombre"
        process = row.get("process") or "Proceso no especificado"
        impact = row.get("impact") or "Impacto no definido"
        effort = row.get("effort_estimate") or "Esfuerzo no estimado"
        rows.append(
            f"- {name} → Proceso: {process} | Impacto: {impact} | Esfuerzo: {effort}"
        )
    return "\n".join(rows)


def summarize_dashboard_inputs(
    processes_df: pd.DataFrame,
    kpis_df: pd.DataFrame,
    pain_points_df: pd.DataFrame,
    automations_df: pd.DataFrame,
) -> str:
    """Aggregate context for dashboard specification prompts."""
    lines = [
        f"Total de procesos modelados: {len(processes_df)}",
        f"Total de KPIs capturados: {len(kpis_df)}",
        f"Total de puntos de dolor: {len(pain_points_df)}",
        f"Total de oportunidades de automatización: {len(automations_df)}",
    ]

    if not kpis_df.empty and "name" in kpis_df.columns:
        sample = kpis_df.head(5)["name"].tolist()
        lines.append(f"KPIs destacados: {', '.join(sample)}")
    if not processes_df.empty and "name" in processes_df.columns:
        lines.append(f"Procesos representativos: {', '.join(processes_df.head(5)['name'].tolist())}")
    if not pain_points_df.empty:
        lines.append("Resumen de puntos de dolor:")
        lines.append(summarize_pain_points(pain_points_df, limit=5))
    if not automations_df.empty:
        lines.append("Automatizaciones mapeadas:")
        lines.append(summarize_automations(automations_df, limit=5))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# UI sections
# ---------------------------------------------------------------------------

def render_dashboard(db_path: str) -> None:
    st.header("Inteligencia General")

    interviews_total = fetch_count(db_path, "interviews")
    pain_points_df = fetch_table(db_path, "pain_points")
    automations_df = fetch_table(db_path, "automation_candidates")

    col1, col2, col3 = st.columns(3)
    col1.metric("Entrevistas procesadas", interviews_total or "—")
    col2.metric("Puntos de dolor", len(pain_points_df))
    col3.metric("Oportunidades de automatización", len(automations_df))

    st.subheader("🔥 Principales puntos de dolor")
    if not pain_points_df.empty:
        st.dataframe(pain_points_df.head(10))
    else:
        st.info("Ejecuta system0 para poblar la tabla de puntos de dolor.")

    st.subheader("🤖 Principales oportunidades de automatización")
    if not automations_df.empty:
        st.dataframe(automations_df.head(10))
    else:
        st.info("Aún no hay automatizaciones registradas en esta base.")


def render_generate_deliverables(db_path: str) -> None:
    st.header("Generar entregables con agentes")

    deliverable = st.selectbox(
        "¿Qué deseas generar?",
        ["Documentación de procesos", "Matriz de priorización", "Especificación de dashboard"],
    )

    if deliverable == "Documentación de procesos":
        render_process_documentation_flow(db_path)
    elif deliverable == "Matriz de priorización":
        render_priority_matrix_flow(db_path)
    else:
        render_dashboard_spec_flow(db_path)


def render_process_documentation_flow(db_path: str) -> None:
    processes_df = fetch_table(db_path, "processes")
    if processes_df.empty or "name" not in processes_df.columns:
        st.warning("No hay procesos disponibles en esta base de datos.")
        return

    process_names = processes_df["name"].dropna().unique().tolist()
    selected_process = st.selectbox("Selecciona un proceso", process_names)

    api_ready = get_anthropic_client() is not None
    if not api_ready:
        st.warning("Configura ANTHROPIC_API_KEY en tu entorno para generar documentación.")

    if st.button("🚀 Generar documentación", type="primary", disabled=not api_ready):
        with st.spinner("Analizando entrevistas consolidadas…"):
            row = processes_df[processes_df["name"] == selected_process].iloc[0]
            context = format_process_for_prompt(row)
            prompt = f"""
Eres un consultor que documenta procesos para Grupo Conversa.

Proceso: {selected_process}
Datos recopilados:
{context}

Genera la documentación en español con:
1. Resumen ejecutivo
2. Descripción del proceso actual
3. Puntos de dolor identificados
4. Oportunidades de automatización
5. Recomendaciones concretas
"""
            try:
                doc = call_claude(prompt, max_tokens=4000)
                st.success("✅ Documentación generada")
                st.markdown(doc)
                st.download_button(
                    "📥 Descargar",
                    data=doc,
                    file_name=f"{selected_process}_documentacion.md",
                    mime="text/markdown",
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"No se pudo generar la documentación: {exc}")


def render_priority_matrix_flow(db_path: str) -> None:
    st.subheader("📊 Matriz de priorización")
    pain_points_df = fetch_table(db_path, "pain_points")
    automations_df = fetch_table(db_path, "automation_candidates")

    if pain_points_df.empty and automations_df.empty:
        st.warning("No hay puntos de dolor ni automatizaciones para analizar.")
        return

    companies_series = (
        pain_points_df["company"] if "company" in pain_points_df.columns else pd.Series([], dtype=str)
    )
    companies = sorted(companies_series.dropna().unique().tolist())
    selected_companies = st.multiselect(
        "Filtrar por empresa",
        options=companies,
        default=companies,
    )

    filtered_pain = pain_points_df
    if selected_companies:
        filtered_pain = pain_points_df[pain_points_df["company"].isin(selected_companies)]

    top_n = st.slider("Número de casos a incluir", min_value=3, max_value=15, value=6)

    api_ready = get_anthropic_client() is not None
    if not api_ready:
        st.warning("Configura ANTHROPIC_API_KEY en tu entorno para generar la matriz.")

    if st.button("🚀 Generar matriz", type="primary", disabled=not api_ready):
        with st.spinner("Construyendo matriz de priorización…"):
            context = f"""
Resumen de puntos de dolor:
{summarize_pain_points(filtered_pain, limit=top_n)}

Resumen de oportunidades de automatización:
{summarize_automations(automations_df, limit=top_n)}
"""
            prompt = f"""
Eres un consultor de transformación para Grupo Conversa.

Usa la información siguiente para crear una matriz de priorización (Impacto vs. Esfuerzo) en español.
Incluye para cada iniciativa: problema, evidencia, impacto esperado, complejidad/ esfuerzo,
áreas involucradas y recomendación de prioridad (Quick Win, High Leverage, etc.).

Contexto:
{context}

Entrega la respuesta como:
1. Resumen ejecutivo
2. Tabla en Markdown con columnas [Prioridad, Problema, Impacto, Esfuerzo, Equipos, KPIs sugeridos]
3. Recomendaciones inmediatas
"""
            try:
                matrix_doc = call_claude(prompt, max_tokens=3500)
                st.success("✅ Matriz generada")
                st.markdown(matrix_doc)
                st.download_button(
                    "📥 Descargar matriz",
                    data=matrix_doc,
                    file_name="matriz_priorizacion.md",
                    mime="text/markdown",
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"No se pudo generar la matriz: {exc}")


def render_dashboard_spec_flow(db_path: str) -> None:
    st.subheader("📈 Especificación de dashboard ejecutivo")

    processes_df = fetch_table(db_path, "processes")
    kpis_df = fetch_table(db_path, "kpis")
    pain_points_df = fetch_table(db_path, "pain_points")
    automations_df = fetch_table(db_path, "automation_candidates")

    if processes_df.empty and kpis_df.empty:
        st.warning("Necesitamos al menos procesos o KPIs para diseñar el dashboard.")
        return

    audience = st.selectbox(
        "Audiencia principal",
        ["Dirección general", "Operaciones", "Transformación digital", "PMO"],
    )
    focus = st.text_area(
        "Enfoque o pregunta clave",
        value="Visibilidad semanal de cuellos de botella y oportunidades de automatización.",
    )

    api_ready = get_anthropic_client() is not None
    if not api_ready:
        st.warning("Configura ANTHROPIC_API_KEY para generar la especificación.")

    if st.button("🚀 Generar especificación", type="primary", disabled=not api_ready):
        with st.spinner("Diseñando dashboard…"):
            context = summarize_dashboard_inputs(
                processes_df=processes_df,
                kpis_df=kpis_df,
                pain_points_df=pain_points_df,
                automations_df=automations_df,
            )
            prompt = f"""
Actúa como diseñador de producto senior para Grupo Conversa.

Audiencia: {audience}
Enfoque clave: {focus}

Datos disponibles:
{context}

Entrega una especificación de dashboard en español con:
1. Objetivo y preguntas que responde
2. Personas usuarias y decisiones que tomarán
3. Fuentes de datos y frecuencia de actualización
4. Wireframe narrativo (secciones, widgets, métricas, filtros)
5. Interacciones clave y alertas
6. KPIs de éxito del dashboard
"""
            try:
                spec_doc = call_claude(prompt, max_tokens=3500)
                st.success("✅ Especificación generada")
                st.markdown(spec_doc)
                st.download_button(
                    "📥 Descargar especificación",
                    data=spec_doc,
                    file_name="dashboard_spec.md",
                    mime="text/markdown",
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"No se pudo generar la especificación: {exc}")


def render_chat() -> None:
    st.header("Chat con la inteligencia de Grupo Conversa")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "¡Hola! Tengo acceso a la inteligencia consolidada. ¿Qué necesitas saber?",
            }
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    client_available = get_anthropic_client() is not None
    if not client_available:
        st.info("Agrega ANTHROPIC_API_KEY para habilitar el chat.")
        return

    if user_input := st.chat_input("Pregunta algo…"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("assistant"):
            with st.spinner("Pensando…"):
                try:
                    response = call_claude(
                        f"Responde en español con datos relevantes de Grupo Conversa. Pregunta: {user_input}",
                        max_tokens=2000,
                    )
                except Exception as exc:  # noqa: BLE001
                    response = f"No pude generar una respuesta: {exc}"
                st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    st.title("🧠 Plataforma de Inteligencia de Grupo Conversa")
    st.caption("Impulsado por system0 y agentes especializados")

    db_paths = list_available_databases()
    if not db_paths:
        st.error("No se encontraron bases de datos en ./data. Ejecuta las extracciones primero.")
        return

    default_index = 0
    for idx, path in enumerate(db_paths):
        if path.as_posix() == DEFAULT_DB_PATH:
            default_index = idx
            break

    db_path = st.sidebar.selectbox(
        "Fuente de datos",
        options=[p.as_posix() for p in db_paths],
        index=default_index if default_index < len(db_paths) else 0,
        format_func=lambda p: f"{Path(p).name} ({Path(p).stat().st_size // 1024} KB)",
    )

    page = st.sidebar.selectbox(
        "Navegación",
        options=["📊 Dashboard", "🤖 Generar entregables", "💬 Chat"],
    )

    if page == "📊 Dashboard":
        render_dashboard(db_path)
    elif page == "🤖 Generar entregables":
        render_generate_deliverables(db_path)
    else:
        render_chat()


if __name__ == "__main__":
    main()
