"""Diagnóstico estrutural de registros de leads.

Este módulo inspeciona a qualidade estrutural dos dados sem modificá-los.

O diagnóstico atual identifica:

- campos presentes;
- campos ausentes;
- campos vazios;
- tipos encontrados;
- campos inesperados;
- problemas estruturais por registro.

Validade de email, telefone, data, duplicidade e classificação serão tratadas
posteriormente em diagnósticos semânticos ou regras de processamento.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .reader import (
    DEFAULT_INPUT_PATH,
    DataReaderError,
    JsonRecord,
    load_json_records,
)


EXPECTED_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "email",
        "phone",
        "company",
        "message",
        "source",
        "created_at",
    }
)


class DiagnosticError(Exception):
    """Erro base para falhas durante a construção do diagnóstico."""


class InvalidDiagnosticRecordError(DiagnosticError):
    """Indica que a entrada do diagnóstico contém um registro inválido."""


@dataclass(frozen=True, slots=True)
class FieldDiagnostic:
    """Estatísticas estruturais de um campo.

    Attributes:
        present: Quantidade de registros que possuem o campo.
        missing: Quantidade de registros que não possuem o campo.
        empty: Quantidade de valores presentes considerados vazios.
        types: Contagem dos tipos Python encontrados.
    """

    present: int
    missing: int
    empty: int
    types: dict[str, int]


@dataclass(frozen=True, slots=True)
class RecordDiagnostic:
    """Problemas estruturais identificados em um registro.

    Attributes:
        position: Posição humana do registro, iniciada em 1.
        issues: Descrições dos problemas encontrados.
    """

    position: int
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    """Resultado completo do diagnóstico estrutural."""

    total_records: int
    expected_fields: tuple[str, ...]
    fields_found: tuple[str, ...]
    unexpected_fields: tuple[str, ...]
    globally_missing_fields: tuple[str, ...]
    field_summary: dict[str, FieldDiagnostic]
    record_issues: tuple[RecordDiagnostic, ...]


@dataclass(slots=True)
class MutableFieldStatistics:
    """Acumulador interno utilizado durante a inspeção dos registros.

    Esta estrutura é mutável apenas durante a construção do relatório.
    O resultado público é convertido posteriormente em ``FieldDiagnostic``,
    que é imutável.
    """

    present: int
    empty: int
    types: Counter[str]


def is_empty_value(value: object) -> bool:
    """Informa se um valor deve ser considerado vazio.

    São considerados vazios:

    - ``None``;
    - string vazia;
    - string contendo somente espaços.

    Coleções vazias não são classificadas como valor vazio nesta etapa.
    Elas serão identificadas como tipos inesperados quando aplicável.

    Args:
        value: Valor que será inspecionado.

    Returns:
        ``True`` quando o valor for vazio; caso contrário, ``False``.
    """
    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    return False


def validate_diagnostic_record(
    record: object,
    position: int,
) -> Mapping[str, Any]:
    """Valida um registro recebido diretamente pelo diagnóstico.

    O leitor já garante que registros vindos do JSON são dicionários.
    Esta validação continua necessária porque ``build_diagnostic`` é uma
    função pública e pode receber dados de testes, generators, APIs ou outras
    fontes.

    Args:
        record: Registro recebido pela função de diagnóstico.
        position: Posição humana do registro, iniciada em 1.

    Returns:
        Registro validado como um mapeamento.

    Raises:
        InvalidDiagnosticRecordError: Se o valor não for um mapeamento.
    """
    if not isinstance(record, Mapping):
        raise InvalidDiagnosticRecordError(
            f"O registro {position} deve ser um mapeamento, "
            f"mas recebeu {type(record).__name__}."
        )

    return record


def create_record_diagnostic(
    record: Mapping[str, Any],
    position: int,
) -> RecordDiagnostic | None:
    """Identifica problemas estruturais de um único registro.

    Args:
        record: Registro que será inspecionado.
        position: Posição humana do registro.

    Returns:
        Diagnóstico do registro ou ``None`` quando não houver problemas.
    """
    issues: list[str] = []

    record_fields = set(record)

    missing_fields = sorted(EXPECTED_FIELDS - record_fields)
    unexpected_fields = sorted(record_fields - EXPECTED_FIELDS)

    for field in missing_fields:
        issues.append(f"campo ausente: {field}")

    for field in sorted(record_fields):
        value = record[field]

        if is_empty_value(value):
            issues.append(f"campo vazio: {field}")

        # None representa ausência de valor e já é contabilizado como vazio.
        # Outros tipos não textuais são destacados separadamente.
        if value is not None and not isinstance(value, str):
            issues.append(
                f"tipo inesperado em {field}: "
                f"{type(value).__name__}"
            )

    for field in unexpected_fields:
        issues.append(f"campo inesperado: {field}")

    if not issues:
        return None

    return RecordDiagnostic(
        position=position,
        issues=tuple(issues),
    )


def update_field_statistics(
    statistics: dict[str, MutableFieldStatistics],
    record: Mapping[str, Any],
) -> None:
    """Atualiza os acumuladores com os campos de um registro.

    A função realiza somente uma passagem pelos valores presentes. Campos
    ausentes são calculados ao final pela diferença entre o total de registros
    e a quantidade de presenças.
    """
    for field, value in record.items():
        field_statistics = statistics.setdefault(
            field,
            MutableFieldStatistics(
                present=0,
                empty=0,
                types=Counter(),
            ),
        )

        field_statistics.present += 1
        field_statistics.types[type(value).__name__] += 1

        if is_empty_value(value):
            field_statistics.empty += 1


def build_diagnostic(
    records: Iterable[Mapping[str, Any]],
) -> DiagnosticReport:
    """Constrói um diagnóstico estrutural em uma única passagem.

    A entrada aceita qualquer ``Iterable``. Portanto, pode receber:

    - listas;
    - tuplas;
    - generators;
    - resultados paginados;
    - registros provenientes de outras fontes.

    O iterable não precisa permitir múltiplas leituras.

    Args:
        records: Fluxo de registros que será analisado.

    Returns:
        Relatório estrutural completo e determinístico.

    Raises:
        InvalidDiagnosticRecordError: Se algum item não for um mapeamento.
    """
    total_records = 0
    fields_found: set[str] = set()
    field_statistics: dict[str, MutableFieldStatistics] = {}
    record_diagnostics: list[RecordDiagnostic] = []

    for position, raw_record in enumerate(records, start=1):
        record = validate_diagnostic_record(raw_record, position)

        total_records += 1
        fields_found.update(record.keys())

        update_field_statistics(field_statistics, record)

        record_diagnostic = create_record_diagnostic(record, position)

        if record_diagnostic is not None:
            record_diagnostics.append(record_diagnostic)

    all_reported_fields = EXPECTED_FIELDS | fields_found

    field_summary: dict[str, FieldDiagnostic] = {}

    for field in sorted(all_reported_fields):
        mutable_statistics = field_statistics.get(field)

        if mutable_statistics is None:
            present = 0
            empty = 0
            type_counts: dict[str, int] = {}
        else:
            present = mutable_statistics.present
            empty = mutable_statistics.empty
            type_counts = dict(sorted(mutable_statistics.types.items()))

        field_summary[field] = FieldDiagnostic(
            present=present,
            missing=total_records - present,
            empty=empty,
            types=type_counts,
        )

    return DiagnosticReport(
        total_records=total_records,
        expected_fields=tuple(sorted(EXPECTED_FIELDS)),
        fields_found=tuple(sorted(fields_found)),
        unexpected_fields=tuple(sorted(fields_found - EXPECTED_FIELDS)),
        globally_missing_fields=tuple(
            sorted(EXPECTED_FIELDS - fields_found)
        ),
        field_summary=field_summary,
        record_issues=tuple(record_diagnostics),
    )


def print_collection(
    title: str,
    values: Sequence[str],
    empty_message: str = "Nenhum",
) -> None:
    """Exibe uma coleção textual de maneira padronizada."""
    print(f"\n{title}:")

    if not values:
        print(f"- {empty_message}")
        return

    for value in values:
        print(f"- {value}")


def print_field_summary(
    field_summary: Mapping[str, FieldDiagnostic],
) -> None:
    """Exibe as estatísticas de cada campo."""
    print("\nResumo por campo:")

    for field, summary in field_summary.items():
        print(f"\nCampo: {field}")
        print(f"  Presentes: {summary.present}")
        print(f"  Ausentes: {summary.missing}")
        print(f"  Vazios: {summary.empty}")
        print(f"  Tipos: {summary.types}")


def print_record_issues(
    record_issues: Sequence[RecordDiagnostic],
) -> None:
    """Exibe os problemas estruturais agrupados por registro."""
    print("\nProblemas por registro:")

    if not record_issues:
        print("- Nenhum problema estrutural encontrado.")
        return

    for diagnostic in record_issues:
        print(f"\nRegistro {diagnostic.position}:")

        for issue in diagnostic.issues:
            print(f"  - {issue}")


def print_diagnostic(report: DiagnosticReport) -> None:
    """Exibe um relatório de diagnóstico no terminal."""
    print("\n=== DIAGNÓSTICO ESTRUTURAL DOS LEADS ===\n")

    print(f"Registros recebidos: {report.total_records}")

    print_collection(
        title="Campos esperados",
        values=report.expected_fields,
    )

    print_collection(
        title="Campos encontrados",
        values=report.fields_found,
    )

    print_collection(
        title="Campos inesperados",
        values=report.unexpected_fields,
    )

    print_collection(
        title="Campos esperados nunca encontrados no arquivo",
        values=report.globally_missing_fields,
    )

    print_field_summary(report.field_summary)
    print_record_issues(report.record_issues)


def build_argument_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do diagnóstico."""
    parser = argparse.ArgumentParser(
        description=(
            "Executa o diagnóstico estrutural de um arquivo JSON "
            "contendo registros de leads."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help=(
            "Caminho do arquivo JSON de entrada. "
            f"Padrão: {DEFAULT_INPUT_PATH}"
        ),
    )

    return parser


def run_diagnostic(file_path: Path) -> int:
    """Executa leitura, diagnóstico e apresentação do relatório."""
    try:
        records: list[JsonRecord] = load_json_records(file_path)
        report = build_diagnostic(records)

    except (DataReaderError, DiagnosticError) as error:
        print(f"Erro ao executar o diagnóstico: {error}")
        return 1

    print_diagnostic(report)

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada do diagnóstico estrutural."""
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    return run_diagnostic(arguments.input)


if __name__ == "__main__":
    raise SystemExit(main())