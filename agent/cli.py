"""
Developer CLI for interacting with the Agentic RAG API (Task 13).

Usage:
    python -m agent.cli --api-key <KEY> --org los_tajibos

Features:
    - Interactive chat loop with colorized output
    - `/reset`, `/sources`, `/stats` commands
    - Session persistence under data/cli_sessions/{session_id}.jsonl
    - Optionally log conversations to a custom file
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import requests

CLI_SESSIONS_DIR = Path("data/cli_sessions")
CLI_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _write_session_event(session_id: str, event: Dict[str, Any]) -> None:
    """Append event to the session JSONL log."""
    log_path = CLI_SESSIONS_DIR / f"{session_id}.jsonl"
    event["timestamp"] = datetime.utcnow().isoformat()
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _append_log_file(path: Optional[Path], message: str) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"{datetime.utcnow().isoformat()} | {message}\n")


def _print_sources(sources: List[Dict[str, Any]]) -> None:
    if not sources:
        click.echo(click.style("No hay fuentes disponibles.", fg="yellow"))
        return

    click.echo(click.style("Fuentes citadas:", fg="cyan"))
    for idx, source in enumerate(sources, start=1):
        score = source.get("score")
        meta = source.get("metadata", {})
        extra = []
        if meta.get("document_title"):
            extra.append(meta["document_title"])
        if meta.get("section"):
            extra.append(f"Sección {meta['section']}")
        if meta.get("entity_type"):
            extra.append(meta["entity_type"])
        detail = " | ".join(extra) if extra else ""
        score_str = f" (score={score:.3f})" if isinstance(score, (int, float)) else ""
        click.echo(f"  {idx}. [{source.get('source_type')}] {detail}{score_str}")


def _print_tool_stats(tool_calls: List[Dict[str, Any]]) -> None:
    if not tool_calls:
        click.echo(click.style("No hay métricas de herramientas.", fg="yellow"))
        return

    click.echo(click.style("Herramientas utilizadas:", fg="cyan"))
    for idx, call in enumerate(tool_calls, start=1):
        name = call.get("tool_name", "desconocido")
        params = call.get("parameters", {})
        result_count = call.get("result_count")
        cache_hit = call.get("cache_hit")
        click.echo(
            f"  {idx}. {name} | resultados={result_count} | cache_hit={cache_hit} | params={params}"
        )


def _build_payload(
    org: str,
    query: str,
    session_id: str,
    context: Optional[str],
    retrieval_mode: str,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "org_id": org,
        "query": query,
        "session_id": session_id,
        "retrieval_mode": retrieval_mode,
    }
    if context:
        payload["context"] = context
    return payload


@click.command()
@click.option("--base-url", default="http://localhost:8000", show_default=True, help="URL base del API RAG")
@click.option("--api-key", envvar="RAG_API_KEY", required=True, help="API key para autenticación")
@click.option("--org", prompt="Organización (org_id)", help="Namespace u organización objetivo")
@click.option("--session", "session_opt", default=None, help="Session ID opcional (se genera uno si no se especifica)")
@click.option("--context", default=None, help="Contexto de negocio opcional (ej. operaciones)")
@click.option(
    "--retrieval-mode",
    type=click.Choice(["auto", "vector", "graph", "hybrid"]),
    default="auto",
    show_default=True,
    help="Modo de recuperación preferido",
)
@click.option("--verbose", is_flag=True, help="Muestra la respuesta JSON completa")
@click.option(
    "--log-file",
    type=click.Path(path_type=Path),
    default=None,
    help="Archivo adicional para registrar la conversación",
)
def main(
    base_url: str,
    api_key: str,
    org: str,
    session_opt: Optional[str],
    context: Optional[str],
    retrieval_mode: str,
    verbose: bool,
    log_file: Optional[Path],
) -> None:
    """
    CLI interactiva para probar el API de chat Agentic RAG.
    """
    chat_url = f"{base_url.rstrip('/')}/chat"
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    session_id = session_opt or str(uuid.uuid4())
    last_response: Optional[Dict[str, Any]] = None

    click.echo(click.style("=== CLI Agentic RAG ===", fg="green"))
    click.echo(f"Base URL: {chat_url}")
    click.echo(f"Org: {org}")
    click.echo(f"Sesión actual: {session_id}")
    click.echo("Comandos: /reset, /sources, /stats, /exit")

    while True:
        try:
            user_input = click.prompt(click.style("Tú", fg="yellow"), prompt_suffix=" > ")
        except (KeyboardInterrupt, EOFError):
            click.echo("\nSaliendo...")
            break

        trimmed = user_input.strip()
        if not trimmed:
            continue

        if trimmed.lower() in {"/exit", "/salir"}:
            click.echo("Hasta luego 👋")
            break

        if trimmed.lower() == "/reset":
            session_id = str(uuid.uuid4())
            click.echo(click.style(f"Nueva sesión: {session_id}", fg="green"))
            continue

        if trimmed.lower() == "/sources":
            if not last_response:
                click.echo(click.style("Aún no hay respuesta para mostrar fuentes.", fg="yellow"))
            else:
                _print_sources(last_response.get("sources", []))
            continue

        if trimmed.lower() == "/stats":
            if not last_response:
                click.echo(click.style("No hay estadísticas todavía.", fg="yellow"))
            else:
                _print_tool_stats(last_response.get("tool_calls", []))
            continue

        payload = _build_payload(org, trimmed, session_id, context, retrieval_mode)
        _append_log_file(log_file, f"SEND {payload}")

        try:
            response = requests.post(chat_url, headers=headers, json=payload, timeout=60)
        except requests.RequestException as exc:
            click.echo(click.style(f"Error de red: {exc}", fg="red"))
            _append_log_file(log_file, f"ERROR {exc}")
            continue

        if response.status_code >= 400:
            detail = response.text
            click.echo(click.style(f"API error ({response.status_code}): {detail}", fg="red"))
            _append_log_file(log_file, f"API_ERROR {detail}")
            continue

        result = response.json()
        last_response = result
        session_id = result.get("session_id", session_id)

        click.echo(click.style("Agente:", fg="cyan"))
        click.echo(result.get("answer", ""))
        click.echo(
            click.style(
                f"[latencia: {result.get('latency_ms', 0):.1f} ms | modelo: {result.get('model')}]",
                fg="blue",
            )
        )
        _print_sources(result.get("sources", []))

        if verbose:
            click.echo(click.style("Respuesta JSON:", fg="magenta"))
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))

        event = {
            "query": trimmed,
            "response": result.get("answer"),
            "sources": result.get("sources", []),
            "tool_calls": result.get("tool_calls", []),
            "latency_ms": result.get("latency_ms"),
            "model": result.get("model"),
        }
        _write_session_event(session_id, event)
        _append_log_file(log_file, f"RECV {json.dumps(result, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
