"""Testes das funções de normalização."""

from __future__ import annotations

import unittest

from src.normalizers import (
    classify_segment,
    normalize_datetime,
    normalize_email,
    normalize_phone,
    normalize_text,
)


class NormalizeTextTests(unittest.TestCase):
    def test_removes_external_and_duplicate_spaces(self) -> None:
        self.assertEqual(
            normalize_text("  Maria   da Silva  "),
            "Maria da Silva",
        )

    def test_empty_text_returns_none(self) -> None:
        self.assertIsNone(normalize_text("   "))
        self.assertIsNone(normalize_text(None))


class NormalizeEmailTests(unittest.TestCase):
    def test_normalizes_valid_email(self) -> None:
        self.assertEqual(
            normalize_email(" MARIA@EXAMPLE.COM "),
            "maria@example.com",
        )

    def test_rejects_invalid_email(self) -> None:
        self.assertIsNone(normalize_email("email-invalido"))


class NormalizePhoneTests(unittest.TestCase):
    def test_keeps_only_digits(self) -> None:
        self.assertEqual(
            normalize_phone("+55 (11) 99999-8888"),
            "5511999998888",
        )


class NormalizeDatetimeTests(unittest.TestCase):
    def test_normalizes_brazilian_date(self) -> None:
        self.assertEqual(
            normalize_datetime("07/01/2026"),
            "2026-01-07T00:00:00",
        )

    def test_normalizes_unix_timestamp(self) -> None:
        result = normalize_datetime("1767225600")

        self.assertIsNotNone(result)
        if result is None:
            self.fail("normalize_datetime should return a string for unix timestamps")

        self.assertIsInstance(result, str)
        self.assertIn("2026", result)

    def test_invalid_date_returns_none(self) -> None:
        self.assertIsNone(normalize_datetime("data inválida"))


class ClassifySegmentTests(unittest.TestCase):
    def test_classifies_demo(self) -> None:
        self.assertEqual(
            classify_segment("Gostaria de agendar uma demonstração"),
            "demo",
        )

    def test_classifies_commercial(self) -> None:
        self.assertEqual(
            classify_segment("Quero conhecer os preços dos planos"),
            "commercial",
        )

    def test_uses_general_as_fallback(self) -> None:
        self.assertEqual(
            classify_segment("Olá, gostaria de conversar"),
            "general",
        )


if __name__ == "__main__":
    unittest.main()