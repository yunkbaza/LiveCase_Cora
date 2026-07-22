"""Diagnóstico estrutural dos registros recebidos."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any


EXPECTED_FIELDS = {
    "name",
    "email",
    "phone",
    "company",
    "message",
    "source",
    "created_at",
}


def is_empty(value: object) -> bool:
    """Verifica se um valor está ausente semanticamente."""
    return value is None or (
        isinstance(value, str) and not value.strip()
    )


def build_diagnostic(
    records: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Gera estatísticas estruturais sem modificar os registros."""
    records_list = list(records)
    all_fields = sorted(
        {
            field
            for record in records_list
            for field in record
        }
        | EXPECTED_FIELDS
    )

    fields: dict[str, dict[str, Any]] = {}

    for field in all_fields:
        present_values = [
            record[field]
            for record in records_list
            if field in record
        ]

        fields[field] = {
            "present": len(present_values),
            "missing": len(records_list) - len(present_values),
            "empty": sum(is_empty(value) for value in present_values),
            "types": dict(
                Counter(
                    type(value).__name__
                    for value in present_values
                )
            ),
        }

    unexpected_fields = sorted(
        set(all_fields) - EXPECTED_FIELDS
    )

    return {
        "total_records": len(records_list),
        "expected_fields": sorted(EXPECTED_FIELDS),
        "unexpected_fields": unexpected_fields,
        "fields": fields,
    }


def print_diagnostic(diagnostic: Mapping[str, Any]) -> None:
    """Apresenta o diagnóstico no terminal."""
    print("\n=== DIAGNÓSTICO ESTRUTURAL ===")
    print(f"\nRegistros recebidos: {diagnostic['total_records']}")

    unexpected = diagnostic["unexpected_fields"]

    print("\nCampos inesperados:")
    if unexpected:
        for field in unexpected:
            print(f"- {field}")
    else:
        print("- Nenhum")

    print("\nResumo por campo:")

    for field, summary in diagnostic["fields"].items():
        print(f"\nCampo: {field}")
        print(f"  Presentes: {summary['present']}")
        print(f"  Ausentes: {summary['missing']}")
        print(f"  Vazios: {summary['empty']}")
        print(f"  Tipos: {summary['types']}")