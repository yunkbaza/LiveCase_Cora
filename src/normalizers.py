"""Funções puras para normalização dos campos dos leads."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Final


EMAIL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)

SUPPORTED_DATE_FORMATS: Final[tuple[str, ...]] = (
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%b %d, %Y",
    "%B %d, %Y",
)

SEGMENT_KEYWORDS: Final[dict[str, tuple[str, ...]]] = {
    "demo": (
        "demo",
        "demonstração",
        "demonstracao",
        "apresentação",
        "apresentacao",
    ),
    "commercial": (
        "preço",
        "preco",
        "valor",
        "orçamento",
        "orcamento",
        "plano",
        "contratar",
        "proposta",
        "comprar",
    ),
    "support": (
        "suporte",
        "problema",
        "erro",
        "falha",
        "não funciona",
        "nao funciona",
        "ajuda",
    ),
    "partnership": (
        "parceria",
        "parceiro",
        "integração",
        "integracao",
        "revenda",
    ),
}


def normalize_text(value: object) -> str | None:
    """Normaliza valores textuais.

    Remove espaços externos e reduz sequências de espaços internos para
    apenas um espaço. Valores ausentes ou vazios retornam ``None``.
    """
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    return " ".join(text.split())


def normalize_email(value: object) -> str | None:
    """Normaliza e valida um endereço de email.

    O email é convertido para letras minúsculas e tem espaços removidos
    das extremidades.

    Returns:
        Email normalizado ou ``None`` quando ausente ou inválido.
    """
    email = normalize_text(value)

    if email is None:
        return None

    email = email.lower()

    if not EMAIL_PATTERN.fullmatch(email):
        return None

    return email


def normalize_phone(value: object) -> str | None:
    """Normaliza o telefone mantendo apenas números.

    O telefone não é utilizado para rejeitar o lead, pois pode ser um campo
    opcional e formatos internacionais podem variar.
    """
    phone = normalize_text(value)

    if phone is None:
        return None

    digits = re.sub(r"\D", "", phone)

    return digits or None


def normalize_datetime(value: object) -> str | None:
    """Converte formatos de data conhecidos para ISO 8601.

    Formatos aceitos:

    - ISO 8601;
    - ``dd/mm/yyyy``;
    - ``yyyy/mm/dd``;
    - ``dd-mm-yyyy``;
    - nomes de meses em inglês;
    - timestamp Unix em segundos.

    Returns:
        Data no formato ISO 8601 ou ``None`` quando não for possível
        interpretá-la.
    """
    text = normalize_text(value)

    if text is None:
        return None

    parsed = _parse_unix_timestamp(text)

    if parsed is None:
        parsed = _parse_iso_datetime(text)

    if parsed is None:
        parsed = _parse_known_formats(text)

    if parsed is None:
        return None

    return parsed.isoformat()


def classify_segment(message: object) -> str:
    """Classifica o interesse do lead com base na mensagem.

    A classificação é determinística e utiliza palavras-chave explícitas.
    Quando nenhuma regra é encontrada, o segmento ``general`` é utilizado.
    """
    normalized_message = normalize_text(message)

    if normalized_message is None:
        return "general"

    searchable_message = normalized_message.casefold()

    for segment, keywords in SEGMENT_KEYWORDS.items():
        if any(keyword in searchable_message for keyword in keywords):
            return segment

    return "general"


def _parse_unix_timestamp(value: str) -> datetime | None:
    """Tenta interpretar uma string numérica como timestamp Unix."""
    if not value.isdigit():
        return None

    try:
        timestamp = int(value)
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _parse_iso_datetime(value: str) -> datetime | None:
    """Tenta interpretar uma data no padrão ISO 8601."""
    normalized_value = value.replace("Z", "+00:00")

    try:
        return datetime.fromisoformat(normalized_value)
    except ValueError:
        return None


def _parse_known_formats(value: str) -> datetime | None:
    """Tenta interpretar formatos alternativos conhecidos."""
    for date_format in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue

    return None