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
    def validate_text(
        self, text: str, filename: str = "download-proxy.yaml"
    ) -> list[tuple[str, str]]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / filename
            path.write_text(text, encoding="utf-8")
            return VALIDATOR.validate_file(path)

    def test_accepts_canonical_domain_rules(self) -> None:
        entries = self.validate_text(
            "payload:\n"
            "  - DOMAIN,download.example.com\n"
            "  - DOMAIN-SUFFIX,xethub.hf.co\n"
        )
        self.assertEqual(
            entries,
            [
                ("DOMAIN", "download.example.com"),
                ("DOMAIN-SUFFIX", "xethub.hf.co"),
            ],
        )

    def test_rejects_keyword_rules(self) -> None:
        with self.assertRaisesRegex(ValueError, "only canonical DOMAIN"):
            self.validate_text("payload:\n  - DOMAIN-KEYWORD,download\n")

    def test_rejects_unapproved_shared_suffix(self) -> None:
        with self.assertRaisesRegex(ValueError, "suffix is not explicitly approved"):
            self.validate_text("payload:\n  - DOMAIN-SUFFIX,googleapis.com\n")

    def test_rejects_broad_service_suffix(self) -> None:
        with self.assertRaisesRegex(ValueError, "suffix is not explicitly approved"):
            self.validate_text("payload:\n  - DOMAIN-SUFFIX,github.com\n")

    def test_suffix_policy_is_file_specific(self) -> None:
        with self.assertRaisesRegex(ValueError, "not explicitly approved"):
            self.validate_text(
                "payload:\n  - DOMAIN-SUFFIX,openai.com\n",
                "download-proxy.yaml",
            )
        entries = self.validate_text(
            "payload:\n  - DOMAIN-SUFFIX,openai.com\n",
            "ai-reality.yaml",
        )
        self.assertEqual(entries, [("DOMAIN-SUFFIX", "openai.com")])

    def test_rejects_secret_markers(self) -> None:
        with self.assertRaisesRegex(ValueError, "possible secret material"):
            self.validate_text("payload:\n  # password: do-not-store-this\n")

    def test_rejects_proxy_server_material_in_comments(self) -> None:
        with self.assertRaisesRegex(ValueError, "possible secret material"):
            self.validate_text("payload:\n  # server: proxy.example.com\n")

    def test_requires_trailing_newline(self) -> None:
        with self.assertRaisesRegex(ValueError, "end with a newline"):
            self.validate_text("payload:\n  - DOMAIN,download.example.com")

    def test_rejects_cross_file_duplicate_domains(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "download-proxy.yaml"
            second = Path(directory) / "download-direct.yaml"
            first.write_text(
                "payload:\n  - DOMAIN,assets.example.com\n", encoding="utf-8"
            )
            second.write_text(
                "payload:\n  - DOMAIN,assets.example.com\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "duplicate domain"):
                VALIDATOR.validate_files([first, second])

    def test_production_rules_cover_observed_hugging_face_cdn(self) -> None:
        entries = VALIDATOR.validate_file(ROOT / "rules/download-proxy.yaml")
        self.assertIn(("DOMAIN", "us.aws.cdn.hf.co"), entries)

    def test_production_ai_rules_do_not_capture_shared_google_parent(self) -> None:
        entries = VALIDATOR.validate_file(ROOT / "rules/ai-reality.yaml")
        self.assertNotIn(("DOMAIN-SUFFIX", "googleapis.com"), entries)
        self.assertIn(
            ("DOMAIN-SUFFIX", "generativelanguage.googleapis.com"), entries
        )


if __name__ == "__main__":
    unittest.main()
