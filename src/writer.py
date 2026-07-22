"""Escrita segura dos resultados do processamento."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DataWriterError(Exception):
    """Erro ao gravar o arquivo de saída."""


def write_json(
    data: dict[str, Any],
    output_path: str | Path,
) -> None:
    """Grava dados JSON utilizando substituição atômica.

    Primeiro o conteúdo é gravado em um arquivo temporário. Depois, o arquivo
    temporário substitui o destino final. Isso reduz o risco de deixar um
    arquivo parcialmente escrito em caso de falha.
    """
    path = Path(output_path)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        with temporary_path.open(
            mode="w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

            file.write("\n")

        temporary_path.replace(path)

    except OSError as error:
        temporary_path.unlink(missing_ok=True)

        raise DataWriterError(
            f"Não foi possível gravar o arquivo {path}: {error}"
        ) from error