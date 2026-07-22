"""Ponto de entrada do pipeline de processamento de leads."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .processor import ProcessResult, process_leads
from .reader import DataReaderError, load_json_records
from .writer import DataWriterError, write_json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "leads_raw.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "output" / "leads_processed.json"


def build_output(result: ProcessResult) -> dict[str, object]:
    """Monta o documento final do processamento."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": result.summary(),
        "leads": result.leads,
        "rejected": result.rejected,
    }


def print_summary(
    result: ProcessResult,
    output_path: Path,
) -> None:
    """Apresenta um resumo amigável no terminal."""
    summary = result.summary()

    print("\n=== PROCESSAMENTO CONCLUÍDO ===\n")
    print(f"Recebidos: {summary['received']}")
    print(f"Processados: {summary['processed']}")
    print(f"Rejeitados: {summary['rejected']}")
    print(
        "Duplicados removidos: "
        f"{summary['duplicates_removed']}"
    )
    print(f"\nArquivo gerado: {output_path.resolve()}")


def build_argument_parser() -> argparse.ArgumentParser:
    """Configura os argumentos aceitos pelo programa."""
    parser = argparse.ArgumentParser(
        description=(
            "Normaliza, valida, classifica e deduplica leads "
            "recebidos em um arquivo JSON."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help="Arquivo JSON de entrada.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Arquivo JSON de saída.",
    )

    return parser


def run(input_path: Path, output_path: Path) -> int:
    """Executa o pipeline completo e retorna um código de saída."""
    try:
        records = load_json_records(input_path)
        result = process_leads(records)

        output = build_output(result)
        write_json(output, output_path)

    except (DataReaderError, DataWriterError) as error:
        print(f"Erro: {error}")
        return 1

    print_summary(result, output_path)

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada da aplicação."""
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    return run(
        input_path=arguments.input,
        output_path=arguments.output,
    )


if __name__ == "__main__":
    raise SystemExit(main())