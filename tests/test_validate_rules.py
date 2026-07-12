from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "validate_rules", ROOT / "scripts/validate_rules.py"
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ValidateRulesTest(unittest.TestCase):
    def validate_text(self, text: str) -> list[tuple[str, str]]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rules.yaml"
            path.write_text(text, encoding="utf-8")
            return VALIDATOR.validate_file(path)

    def test_accepts_canonical_domain_rules(self) -> None:
        entries = self.validate_text(
            "payload:\n"
            "  - DOMAIN,download.example.com\n"
            "  - DOMAIN-SUFFIX,models.example.org\n"
        )
        self.assertEqual(
            entries,
            [
                ("DOMAIN", "download.example.com"),
                ("DOMAIN-SUFFIX", "models.example.org"),
            ],
        )

    def test_rejects_keyword_rules(self) -> None:
        with self.assertRaisesRegex(ValueError, "only canonical DOMAIN"):
            self.validate_text("payload:\n  - DOMAIN-KEYWORD,download\n")

    def test_rejects_over_broad_shared_suffix(self) -> None:
        with self.assertRaisesRegex(ValueError, "over-broad shared suffix"):
            self.validate_text("payload:\n  - DOMAIN-SUFFIX,googleapis.com\n")

    def test_rejects_secret_markers(self) -> None:
        with self.assertRaisesRegex(ValueError, "possible secret material"):
            self.validate_text("payload:\n  # password: do-not-store-this\n")

    def test_requires_trailing_newline(self) -> None:
        with self.assertRaisesRegex(ValueError, "end with a newline"):
            self.validate_text("payload:\n  - DOMAIN,download.example.com")


if __name__ == "__main__":
    unittest.main()
