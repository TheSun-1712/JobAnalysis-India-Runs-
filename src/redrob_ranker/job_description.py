from __future__ import annotations

import re
from dataclasses import dataclass, field


from .config import (
    CONSULTING_COMPANIES,
    RELEVANT_TITLE_PATTERNS,
    ROLE_TERMS,
    INDIA_TIER1_MARKERS,
    PRODUCT_COMPANY_HINTS,
)


@dataclass(frozen=True)
class JobDescriptionProfile:
    title: str
    location_text: str
    country_text: str
    work_mode: str
    experience_min: float
    experience_max: float
    target_experience: float
    required_terms: dict[str, float] = field(default_factory=dict)
    desired_terms: dict[str, float] = field(default_factory=dict)
    disqualifier_terms: tuple[str, ...] = ()
    location_terms: tuple[str, ...] = ()


def _extract_experience(text: str) -> tuple[float, float, float]:
    match = re.search(r"(\d+(?:\.\d+)?)\s*[–-]\s*(\d+(?:\.\d+)?)\s*years", text, re.I)
    if match:
        low = float(match.group(1))
        high = float(match.group(2))
    else:
        low, high = 5.0, 9.0
    return low, high, (low + high) / 2.0


def _extract_location_terms(text: str) -> tuple[str, ...]:
    found = []
    lowered = text.lower()
    for marker in INDIA_TIER1_MARKERS:
        if marker in lowered:
            found.append(marker)
    if "tier-1" in lowered:
        found.append("tier-1")
    return tuple(dict.fromkeys(found))


def _extract_required_terms(text: str) -> dict[str, float]:
    required: dict[str, float] = {}
    for term, weight in ROLE_TERMS.items():
        if term in text.lower():
            required[term] = weight
    return required


def parse_job_description(text: str) -> JobDescriptionProfile:
    lowered = text.lower()
    title_match = re.search(r"job description:\s*(.+)", text, re.I)
    title = title_match.group(1).strip() if title_match else "Senior AI Engineer"
    exp_min, exp_max, target = _extract_experience(text)
    location_match = re.search(r"location:\s*(.+)", text, re.I)
    location_text = location_match.group(1).strip() if location_match else "Pune/Noida, India"
    country_text = "india" if "india" in lowered else ""
    work_mode = "hybrid" if "hybrid" in lowered else "flexible"

    required = _extract_required_terms(text)
    desired = {}
    for term in ("product", "evaluation", "ab test", "recruiter", "ranking", "retrieval", "embeddings", "vector database", "python"):
        if term in lowered:
            desired[term] = ROLE_TERMS.get(term, 1.0)

    disqualifiers = (
        "pure research",
        "langchain",
        "consulting",
        "services",
        "framework",
        "robotics",
        "computer vision",
        "speech",
    )

    return JobDescriptionProfile(
        title=title,
        location_text=location_text,
        country_text=country_text,
        work_mode=work_mode,
        experience_min=exp_min,
        experience_max=exp_max,
        target_experience=target,
        required_terms=required,
        desired_terms=desired,
        disqualifier_terms=disqualifiers,
        location_terms=_extract_location_terms(text),
    )
