#!/usr/bin/env python3
"""Validate the intentionally small public Mihomo rule-provider files."""

from __future__ import annotations

import ipaddress
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RULE_FILES = (
    ROOT / "rules/download-proxy.yaml",
    ROOT / "rules/download-direct.yaml",
)
MAX_FILE_SIZE = 65_536
MAX_RULES_PER_FILE = 256
RULE_RE = re.compile(r"^  - (DOMAIN|DOMAIN-SUFFIX),([a-z0-9.-]+)$")
LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"
)
SECRET_MARKERS = (
    "password:",
    "private-key:",
    "private_key:",
    "authorization:",
    "bearer ",
    "BEGIN PRIVATE KEY",
)
APPROVED_SUFFIXES = {
    "civitai.com",
    "kaggleusercontent.com",
    "modelscope.ai",
    "modelscope.cn",
    "xethub.hf.co",
}


def fail(message: str) -> None:
    raise ValueError(message)


def validate_domain(path: Path, line_number: int, domain: str) -> None:
    if domain != domain.lower():
        fail(f"{path}:{line_number}: domain must be lowercase: {domain}")
    if domain.startswith(".") or domain.endswith(".") or ".." in domain:
        fail(f"{path}:{line_number}: invalid domain: {domain}")
    if len(domain) > 253 or "." not in domain:
        fail(f"{path}:{line_number}: invalid domain length or shape: {domain}")
    if any(not LABEL_RE.fullmatch(label) for label in domain.split(".")):
        fail(f"{path}:{line_number}: invalid domain label: {domain}")
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        return
    fail(f"{path}:{line_number}: IP literals are not allowed: {domain}")


def validate_file(path: Path) -> list[tuple[str, str]]:
    if not path.is_file():
        fail(f"missing required rule file: {path}")
    raw = path.read_bytes()
    if len(raw) > MAX_FILE_SIZE:
        fail(f"{path}: exceeds {MAX_FILE_SIZE} bytes")
    if raw and not raw.endswith(b"\n"):
        fail(f"{path}: file must end with a newline")
    text = raw.decode("utf-8")
    lower_text = text.lower()
    if UUID_RE.search(text) or any(marker.lower() in lower_text for marker in SECRET_MARKERS):
        fail(f"{path}: possible secret material detected")

    entries: list[tuple[str, str]] = []
    saw_payload = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not saw_payload:
            if line != "payload:":
                fail(f"{path}:{line_number}: first content line must be 'payload:'")
            saw_payload = True
            continue
        match = RULE_RE.fullmatch(line)
        if not match:
            fail(
                f"{path}:{line_number}: only canonical DOMAIN and DOMAIN-SUFFIX "
                "entries are allowed"
            )
        rule_type, domain = match.groups()
        validate_domain(path, line_number, domain)
        if rule_type == "DOMAIN-SUFFIX" and domain not in APPROVED_SUFFIXES:
            fail(f"{path}:{line_number}: suffix is not explicitly approved: {domain}")
        entries.append((rule_type, domain))

    if not saw_payload or not entries:
        fail(f"{path}: payload must contain at least one rule")
    if len(entries) > MAX_RULES_PER_FILE:
        fail(f"{path}: exceeds {MAX_RULES_PER_FILE} rules")
    return entries


def main() -> int:
    seen: dict[tuple[str, str], Path] = {}
    total = 0
    try:
        for path in RULE_FILES:
            entries = validate_file(path)
            for entry in entries:
                if entry in seen:
                    fail(f"duplicate rule in {seen[entry]} and {path}: {entry[0]},{entry[1]}")
                seen[entry] = path
            total += len(entries)
            print(f"validated {path.relative_to(ROOT)}: {len(entries)} rules")
    except (UnicodeDecodeError, ValueError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"validation passed: {total} rules across {len(RULE_FILES)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
