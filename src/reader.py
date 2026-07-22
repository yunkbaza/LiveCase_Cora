"""Leitura e validação estrutural de arquivos JSON com registros de leads.

Este módulo é responsável exclusivamente pela camada de extração:

- localizar e abrir o arquivo;
- interpretar o conteúdo JSON;
- validar a estrutura raiz;
- validar que cada item é um objeto JSON;
- retornar os registros sem aplicar regras de negócio.

Normalização, validação de email, deduplicação e classificação não pertencem
a este módulo.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


JsonRecord = dict[str, Any]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "leads_raw.json"


class DataReaderError(Exception):
    """Erro base para falhas relacionadas à leitura da fonte de dados."""


class DataFileNotFoundError(DataReaderError):
    """Indica que o arquivo de entrada não foi encontrado."""


class InvalidFilePathError(DataReaderError):
    """Indica que o caminho recebido não representa um arquivo regular."""


class FileAccessError(DataReaderError):
    """Indica que o arquivo não pôde ser acessado ou decodificado."""


class InvalidJsonError(DataReaderError):
    """Indica que o arquivo não contém um documento JSON válido."""


class InvalidRootStructureError(DataReaderError):
    """Indica que a raiz do JSON não é uma lista."""


class InvalidRecordError(DataReaderError):
    """Indica que um item da lista não é um objeto JSON."""


def validate_input_path(file_path: Path) -> None:
    """Valida se o caminho de entrada existe e representa um arquivo.

    Args:
        file_path: Caminho que será utilizado para leitura.

    Raises:
        DataFileNotFoundError: Se o caminho não existir.
        InvalidFilePathError: Se o caminho não representar um arquivo regular.
    """
    if not file_path.exists():
        raise DataFileNotFoundError(
            f"Arquivo de entrada não encontrado: {file_path}"
        )

    if not file_path.is_file():
        raise InvalidFilePathError(
            f"O caminho de entrada não representa um arquivo: {file_path}"
        )


def read_json_document(file_path: Path) -> object:
    """Abre e interpreta um documento JSON.

    A função retorna ``object`` porque a estrutura raiz ainda não foi
    validada nesta etapa. Essa validação é feita separadamente para manter
    cada função com uma única responsabilidade.

    O encoding ``utf-8-sig`` aceita tanto UTF-8 convencional quanto arquivos
    que contenham BOM no início, sem alterar o comportamento para arquivos
    UTF-8 normais.

    Args:
        file_path: Caminho do documento JSON.

    Returns:
        Conteúdo Python produzido pelo parser JSON.

    Raises:
        InvalidJsonError: Se o documento não contiver JSON válido.
        FileAccessError: Se o arquivo não puder ser lido ou decodificado.
    """
    try:
        with file_path.open(mode="r", encoding="utf-8-sig") as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise InvalidJsonError(
            "O arquivo não contém um JSON válido. "
            f"Linha {error.lineno}, coluna {error.colno}: {error.msg}."
        ) from error

    except PermissionError as error:
        raise FileAccessError(
            f"Sem permissão para ler o arquivo: {file_path}"
        ) from error

    except UnicodeDecodeError as error:
        raise FileAccessError(
            f"O arquivo não está codificado corretamente em UTF-8: {file_path}"
        ) from error

    except OSError as error:
        raise FileAccessError(
            f"Não foi possível acessar o arquivo {file_path}: {error}"
        ) from error


def validate_json_records(document: object) -> list[JsonRecord]:
    """Valida o contrato estrutural do documento carregado.

    O contrato de entrada atual exige:

    - raiz JSON representada por uma lista;
    - cada item da lista representado por um objeto JSON.

    Os campos internos não são validados aqui. Um registro pode ter campos
    ausentes, vazios ou inesperados e ainda assim ser estruturalmente legível.

    Args:
        document: Conteúdo já interpretado pelo parser JSON.

    Returns:
        Lista de registros JSON.

    Raises:
        InvalidRootStructureError: Se a raiz não for uma lista.
        InvalidRecordError: Se algum item não for um dicionário.
    """
    if not isinstance(document, list):
        raise InvalidRootStructureError(
            "A raiz do JSON deve ser uma lista de registros."
        )

    records: list[JsonRecord] = []

    for index, item in enumerate(document):
        if not isinstance(item, dict):
            raise InvalidRecordError(
                "Todos os itens da lista devem ser objetos JSON. "
                f"O item no índice {index} possui o tipo "
                f"{type(item).__name__}."
            )

        records.append(item)

    return records


def load_json_records(file_path: str | Path) -> list[JsonRecord]:
    """Carrega e valida registros de um arquivo JSON.

    Esta é a função pública principal do módulo. Ela coordena a validação
    do caminho, a leitura do documento e a validação da estrutura.

    Args:
        file_path: Caminho do arquivo, como ``str`` ou ``Path``.

    Returns:
        Lista de registros exatamente como foram recebidos no JSON.

    Raises:
        DataReaderError: Para qualquer falha de leitura ou estrutura.
    """
    normalized_path = Path(file_path).expanduser()

    validate_input_path(normalized_path)

    document = read_json_document(normalized_path)

    return validate_json_records(document)


def build_argument_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos da execução do módulo."""
    parser = argparse.ArgumentParser(
        description=(
            "Lê um arquivo JSON e valida se ele contém uma lista "
            "de registros."
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


def run_reader(file_path: Path) -> int:
    """Executa a leitura e apresenta um resumo no terminal.

    Args:
        file_path: Caminho do arquivo que será lido.

    Returns:
        Código de saída do processo: zero para sucesso e um para erro.
    """
    try:
        records = load_json_records(file_path)
    except DataReaderError as error:
        print(f"Erro ao carregar os dados: {error}")
        return 1

    print("Arquivo carregado com sucesso.")
    print(f"Caminho: {file_path.resolve()}")
    print(f"Registros recebidos: {len(records)}")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada do módulo de leitura."""
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    return run_reader(arguments.input)


if __name__ == "__main__":
    raise SystemExit(main())