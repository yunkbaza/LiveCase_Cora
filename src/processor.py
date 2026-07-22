"""Aplicação das regras de negócio sobre os registros de leads."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .normalizers import (
    classify_segment,
    normalize_datetime,
    normalize_email,
    normalize_phone,
    normalize_text,
)


RawRecord = Mapping[str, Any]
NormalizedRecord = dict[str, Any]


@dataclass(frozen=True, slots=True)
class ProcessResult:
    """Resultado completo do processamento."""

    leads: list[NormalizedRecord]
    rejected: list[dict[str, Any]]
    received: int
    duplicates_removed: int

    @property
    def processed(self) -> int:
        """Quantidade final de leads válidos e únicos."""
        return len(self.leads)

    @property
    def rejected_count(self) -> int:
        """Quantidade de registros rejeitados."""
        return len(self.rejected)

    def summary(self) -> dict[str, int]:
        """Retorna os principais indicadores do processamento."""
        return {
            "received": self.received,
            "processed": self.processed,
            "rejected": self.rejected_count,
            "duplicates_removed": self.duplicates_removed,
        }


def process_leads(records: Iterable[RawRecord]) -> ProcessResult:
    """Normaliza, valida e deduplica um fluxo de leads.

    Fluxo aplicado:

    1. normalização individual;
    2. rejeição de registros inválidos;
    3. deduplicação pelo email normalizado;
    4. seleção do registro mais recente.

    Args:
        records: Registros de qualquer fonte iterável.

    Returns:
        Leads válidos, registros rejeitados e resumo do processamento.
    """
    received = 0
    rejected: list[dict[str, Any]] = []
    leads_by_email: dict[str, NormalizedRecord] = {}
    duplicates_removed = 0

    for position, raw_record in enumerate(records, start=1):
        received += 1

        normalized, rejection_reasons = normalize_lead(raw_record)

        if rejection_reasons:
            rejected.append(
                {
                    "position": position,
                    "reasons": rejection_reasons,
                    "record": dict(raw_record),
                }
            )
            continue

        email = normalized["email"]
        existing = leads_by_email.get(email)

        if existing is None:
            leads_by_email[email] = normalized
            continue

        duplicates_removed += 1

        if is_newer(normalized, existing):
            leads_by_email[email] = normalized

    leads = sorted(
        leads_by_email.values(),
        key=lambda lead: (
            lead["created_at"],
            lead["email"],
        ),
    )

    return ProcessResult(
        leads=leads,
        rejected=rejected,
        received=received,
        duplicates_removed=duplicates_removed,
    )


def normalize_lead(
    record: RawRecord,
) -> tuple[NormalizedRecord, list[str]]:
    """Normaliza um registro e retorna possíveis motivos de rejeição.

    A função não modifica o registro original.
    """
    rejection_reasons: list[str] = []

    raw_email = record.get("email")
    email = normalize_email(raw_email)

    if normalize_text(raw_email) is None:
        rejection_reasons.append("missing_email")
    elif email is None:
        rejection_reasons.append("invalid_email")

    created_at = normalize_datetime(record.get("created_at"))

    if created_at is None:
        rejection_reasons.append("invalid_created_at")

    name = normalize_text(
        record.get("name") or record.get("nome")
    )

    normalized: NormalizedRecord = {
        "name": name,
        "email": email,
        "phone": normalize_phone(record.get("phone")),
        "company": normalize_text(record.get("company")),
        "message": normalize_text(record.get("message")),
        "source": normalize_text(record.get("source")),
        "created_at": created_at,
        "segment": classify_segment(record.get("message")),
    }

    return normalized, rejection_reasons


def is_newer(
    candidate: NormalizedRecord,
    current: NormalizedRecord,
) -> bool:
    """Informa se um lead duplicado é mais recente que o armazenado.

    Em caso de empate, o primeiro registro permanece. Essa escolha torna o
    resultado determinístico e evita substituições sem benefício.
    """
    candidate_date = datetime.fromisoformat(candidate["created_at"])
    current_date = datetime.fromisoformat(current["created_at"])

    return candidate_date > current_date