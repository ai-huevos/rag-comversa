#!/usr/bin/env python3
"""
Script para ejecutar todas las pruebas del agente RAG (Task 10)
Proporciona resumen de cobertura y resultados.

Uso:
    python tests/run_agent_tests.py              # Ejecutar todas las pruebas
    python tests/run_agent_tests.py --verbose    # Modo verbose
    python tests/run_agent_tests.py --coverage   # Con reporte de cobertura
"""
import sys
import subprocess
from pathlib import Path


def run_tests(verbose: bool = False, coverage: bool = False):
    """Ejecutar pruebas del agente RAG"""
    print("=" * 70)
    print("Pruebas del Agente RAG (Task 10)")
    print("=" * 70)
    print()

    # Archivos de prueba
    test_files = [
        "tests/test_agent_session.py",
        "tests/test_agent_telemetry.py",
        "tests/test_agent_rag_agent.py",
        "tests/test_agent_integration.py",
    ]

    # Construir comando pytest
    cmd = ["python3", "-m", "pytest"]

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    if coverage:
        cmd.extend([
            "--cov=agent",
            "--cov-report=term-missing",
            "--cov-report=html:reports/agent_coverage",
        ])

    cmd.extend(test_files)

    print(f"Ejecutando: {' '.join(cmd)}")
    print()

    # Ejecutar pytest
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)

    print()
    print("=" * 70)

    if result.returncode == 0:
        print("✅ Todas las pruebas pasaron exitosamente")
        if coverage:
            print(f"📊 Reporte de cobertura: reports/agent_coverage/index.html")
    else:
        print("❌ Algunas pruebas fallaron")
        print(f"Código de salida: {result.returncode}")

    print("=" * 70)

    return result.returncode


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Ejecutar pruebas del agente RAG (Task 10)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Modo verbose con más detalles",
    )
    parser.add_argument(
        "--coverage",
        "-c",
        action="store_true",
        help="Generar reporte de cobertura",
    )

    args = parser.parse_args()

    exit_code = run_tests(verbose=args.verbose, coverage=args.coverage)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
