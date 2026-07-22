"""Testes das regras principais do processamento."""

from __future__ import annotations

import unittest

from src.processor import process_leads


class ProcessLeadsTests(unittest.TestCase):
    def test_rejects_missing_email(self) -> None:
        records = [
            {
                "name": "Maria",
                "created_at": "2026-01-01",
            }
        ]

        result = process_leads(records)

        self.assertEqual(result.received, 1)
        self.assertEqual(result.processed, 0)
        self.assertEqual(result.rejected_count, 1)
        self.assertIn(
            "missing_email",
            result.rejected[0]["reasons"],
        )

    def test_rejects_invalid_email(self) -> None:
        records = [
            {
                "email": "email-invalido",
                "created_at": "2026-01-01",
            }
        ]

        result = process_leads(records)

        self.assertEqual(result.rejected_count, 1)
        self.assertIn(
            "invalid_email",
            result.rejected[0]["reasons"],
        )

    def test_uses_nome_as_name_alias(self) -> None:
        records = [
            {
                "nome": "Lucia",
                "email": "lucia@example.com",
                "created_at": "2026-01-01",
            }
        ]

        result = process_leads(records)

        self.assertEqual(result.processed, 1)
        self.assertEqual(result.leads[0]["name"], "Lucia")

    def test_keeps_most_recent_duplicate(self) -> None:
        records = [
            {
                "name": "Maria Antiga",
                "email": "maria@example.com",
                "created_at": "2026-01-01",
            },
            {
                "name": "Maria Atual",
                "email": " MARIA@EXAMPLE.COM ",
                "created_at": "2026-02-01",
            },
        ]

        result = process_leads(records)

        self.assertEqual(result.processed, 1)
        self.assertEqual(result.duplicates_removed, 1)
        self.assertEqual(
            result.leads[0]["name"],
            "Maria Atual",
        )

    def test_does_not_modify_original_record(self) -> None:
        record = {
            "email": " USER@EXAMPLE.COM ",
            "created_at": "01/01/2026",
        }

        original = record.copy()

        process_leads([record])

        self.assertEqual(record, original)


if __name__ == "__main__":
    unittest.main()