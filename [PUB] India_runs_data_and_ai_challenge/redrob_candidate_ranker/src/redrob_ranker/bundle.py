from __future__ import annotations

import gzip
import json
import re
import zipfile
from pathlib import Path
from typing import Iterable


def open_text_stream(path: Path):
    suffixes = "".join(path.suffixes).lower()
    if suffixes.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open("rt", encoding="utf-8", newline="")


def iter_candidate_records(path: str | Path) -> Iterable[dict]:
    source = Path(path)
    with open_text_stream(source) as handle:
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line)


def extract_docx_text(path: str | Path) -> str:
    source = Path(path)
    with zipfile.ZipFile(source) as archive:
        xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    xml = xml.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'")
    lines = [line.strip() for line in xml.splitlines() if line.strip()]
    return "\n".join(lines)


def flatten_candidate_text(candidate: dict) -> str:
    profile = candidate.get("profile", {})
    history = candidate.get("career_history", [])
    education = candidate.get("education", [])
    skills = candidate.get("skills", [])
    certifications = candidate.get("certifications", [])
    languages = candidate.get("languages", [])
    signals = candidate.get("redrob_signals", {})

    parts: list[str] = []
    for key in ("headline", "summary", "current_title", "current_company", "location", "country", "current_industry"):
        value = profile.get(key)
        if value:
            parts.append(str(value))

    for item in history:
        for key in ("company", "title", "industry", "description"):
            value = item.get(key)
            if value:
                parts.append(str(value))

    for item in education:
        for key in ("institution", "degree", "field_of_study", "grade", "tier"):
            value = item.get(key)
            if value:
                parts.append(str(value))

    for item in skills:
        for key in ("name", "proficiency"):
            value = item.get(key)
            if value:
                parts.append(str(value))

    for item in certifications:
        for key in ("name", "issuer"):
            value = item.get(key)
            if value:
                parts.append(str(value))

    for item in languages:
        for key in ("language", "proficiency"):
            value = item.get(key)
            if value:
                parts.append(str(value))

    for key, value in signals.items():
        if key == "skill_assessment_scores" and isinstance(value, dict):
            parts.extend(map(str, value.keys()))
        elif isinstance(value, dict):
            parts.extend(str(v) for v in value.values())
        else:
            parts.append(str(value))

    return " ".join(parts).lower()
