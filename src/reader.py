"""Leitura e validação estrutural de arquivos JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


JsonRecord = dict[str, Any]


class DataReaderError(Exception):
    """Erro ao carregar ou validar a fonte de dados."""


def load_json_records(file_path: str | Path) -> list[JsonRecord]:
    """Carrega uma lista de objetos JSON.

    Args:
        file_path: Caminho do arquivo de entrada.

    Returns:
        Lista de registros encontrados no arquivo.

    Raises:
        DataReaderError: Quando o arquivo não pode ser lido ou possui
        uma estrutura inválida.
    """
    path = Path(file_path)

    if not path.is_file():
        raise DataReaderError(f"Arquivo não encontrado: {path}")

    try:
        with path.open("r", encoding="utf-8-sig") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise DataReaderError(
            f"JSON inválido na linha {error.lineno}, "
            f"coluna {error.colno}: {error.msg}"
        ) from error
    except OSError as error:
        raise DataReaderError(
            f"Não foi possível ler o arquivo: {error}"
        ) from error

    if not isinstance(data, list):
        raise DataReaderError(
            "A raiz do JSON deve ser uma lista de registros."
        )

    for index, record in enumerate(data):
        if not isinstance(record, dict):
            raise DataReaderError(
                f"O registro no índice {index} deve ser um objeto JSON."
            )

    return data