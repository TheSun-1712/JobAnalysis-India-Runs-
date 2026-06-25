from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from .bundle import flatten_candidate_text
from .job_description import (
    CONSULTING_COMPANIES,
    INDIA_TIER1_MARKERS,
    PRODUCT_COMPANY_HINTS,
    JobDescriptionProfile,
    RELEVANT_TITLE_PATTERNS,
)


TITLE_NORMALIZATION = {
    "ai specialist": "ai engineer",
    "machine learning engineer": "ml engineer",
    "recommendation systems engineer": "recommendation engineer",
    "ai research engineer": "ai engineer",
    "senior machine learning engineer": "ml engineer",
    "senior data engineer": "data engineer",
    "senior software engineer": "software engineer",
    "full stack developer": "software engineer",
}


RELEVANT_SKILLS = {
    "python",
    "sql",
    "spark",
    "airflow",
    "dbt",
    "pyspark",
    "nlp",
    "llm",
    "llms",
    "embeddings",
    "retrieval",
    "ranking",
    "vector search",
    "vector database",
    "milvus",
    "pinecone",
    "weaviate",
    "qdrant",
    "faiss",
    "elasticsearch",
    "opensearch",
    "learning to rank",
    "lora",
    "qlora",
    "peft",
    "evaluation",
    "ndcg",
    "mrr",
    "map",
    "ab testing",
    "a/b testing",
    "recommender systems",
    "recommendation systems",
    "fine-tuning llms",
    "bentoml",
}


BAD_BACKGROUND_HINTS = {
    "consultant",
    "consulting",
    "sales",
    "recruiter",
    "teacher",
    "writer",
    "designer",
    "accountant",
    "hr manager",
    "customer support",
    "operations manager",
}


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: dict[str, Any]
    score: float
    raw_score: float
    reason: str


def _candidate_number(candidate_id: str) -> int:
    try:
        return int(candidate_id.split("_")[-1])
    except Exception:
        return 10**9


def _token_counter(text: str) -> Counter[str]:
    tokens = re.findall(r"[a-z0-9\+\#\-/']+", text.lower())
    return Counter(tokens)


def _gaussian(value: float, center: float, sigma: float) -> float:
    if sigma <= 0:
        return 0.0
    return math.exp(-((value - center) ** 2) / (2.0 * sigma * sigma))


def _experience_score(years: float, jd: JobDescriptionProfile) -> float:
    center = jd.target_experience
    base = _gaussian(years, center, 2.1)
    if years < jd.experience_min:
        base *= 0.55
    elif years > jd.experience_max + 3:
        base *= 0.7
    return base


def _title_score(candidate: dict[str, Any]) -> tuple[float, str]:
    title = str(candidate.get("profile", {}).get("current_title", "")).lower()
    normalized = TITLE_NORMALIZATION.get(title, title)
    for pattern, score in RELEVANT_TITLE_PATTERNS.items():
        if pattern in normalized:
            return score, pattern
    return 0.0, ""


def _product_background_score(candidate: dict[str, Any]) -> float:
    history = candidate.get("career_history", [])
    if not history:
        return 0.0
    product_hits = 0
    consulting_hits = 0
    technical_hits = 0
    for item in history:
        company = str(item.get("company", "")).lower()
        title = str(item.get("title", "")).lower()
        text = f"{company} {title} {item.get('industry', '')}".lower()
        if any(hint in text for hint in PRODUCT_COMPANY_HINTS):
            product_hits += 1
        if any(hint in text for hint in CONSULTING_COMPANIES):
            consulting_hits += 1
        if any(hint in title for hint in ("engineer", "scientist", "analyst", "developer", "architect")):
            technical_hits += 1
    score = 0.15 * product_hits + 0.1 * technical_hits - 0.12 * consulting_hits
    if consulting_hits and product_hits == 0:
        score -= 0.25
    return max(-0.4, min(0.45, score))


def _location_fit(candidate: dict[str, Any], jd: JobDescriptionProfile) -> float:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    location = f"{profile.get('location', '')} {profile.get('country', '')}".lower()
    preferred = any(marker in location for marker in INDIA_TIER1_MARKERS)
    india = "india" in location
    relocate = bool(signals.get("willing_to_relocate"))
    mode = str(signals.get("preferred_work_mode", "")).lower()
    bonus = 0.0
    if preferred or india:
        bonus += 0.18
    elif relocate:
        bonus += 0.06
    else:
        bonus -= 0.12
    if jd.work_mode == "hybrid" and mode in {"hybrid", "flexible", "onsite"}:
        bonus += 0.08
    elif jd.work_mode == "remote" and mode in {"remote", "flexible"}:
        bonus += 0.08
    elif jd.work_mode == "onsite" and mode == "onsite":
        bonus += 0.08
    return max(-0.3, min(0.32, bonus))


def _availability_score(candidate: dict[str, Any]) -> float:
    signals = candidate.get("redrob_signals", {})
    profile = candidate.get("profile", {})
    score = 0.0
    if signals.get("open_to_work_flag"):
        score += 0.18
    score += min(0.12, float(signals.get("recruiter_response_rate", 0.0)) * 0.16)
    score += min(0.08, max(0.0, 1.0 - float(signals.get("avg_response_time_hours", 999.0)) / 240.0) * 0.08)
    score += min(0.06, float(signals.get("interview_completion_rate", 0.0)) * 0.06)
    notice = float(signals.get("notice_period_days", 180))
    if notice <= 30:
        score += 0.12
    elif notice <= 60:
        score += 0.05
    elif notice <= 90:
        score += 0.0
    else:
        score -= 0.08
    if signals.get("verified_email"):
        score += 0.04
    if signals.get("verified_phone"):
        score += 0.04
    if signals.get("linkedin_connected"):
        score += 0.02
    if profile.get("years_of_experience", 0) >= 5:
        score += 0.02
    return max(-0.15, min(0.55, score))


def _plausibility_score(candidate: dict[str, Any]) -> float:
    profile = candidate.get("profile", {})
    history = candidate.get("career_history", [])
    signals = candidate.get("redrob_signals", {})
    years = float(profile.get("years_of_experience", 0.0))
    career_years = sum(float(item.get("duration_months", 0)) for item in history) / 12.0
    delta = abs(career_years - years)
    score = 0.18
    if delta <= 1.0:
        score += 0.16
    elif delta <= 2.5:
        score += 0.08
    elif delta <= 4.0:
        score -= 0.02
    else:
        score -= 0.14

    completeness = float(signals.get("profile_completeness_score", 0.0))
    score += min(0.08, completeness / 200.0)
    if float(signals.get("github_activity_score", -1.0)) >= 0:
        score += 0.03
    if float(signals.get("search_appearance_30d", 0)) > 0:
        score += 0.02
    if float(signals.get("saved_by_recruiters_30d", 0)) > 0:
        score += 0.02
    return max(-0.2, min(0.45, score))


def _skill_score(candidate: dict[str, Any], text: str) -> tuple[float, list[str]]:
    skills = candidate.get("skills", [])
    matched: list[str] = []
    score = 0.0
    lowered = text.lower()
    for skill in skills:
        name = str(skill.get("name", "")).strip()
        if not name:
            continue
        name_l = name.lower()
        if name_l in RELEVANT_SKILLS or any(token in name_l for token in ("python", "sql", "spark", "airflow", "llm", "embedding", "retrieval", "ranking", "vector", "milvus", "faiss", "qdrant", "weaviate", "pinecone", "ndcg", "mrr", "map", "ab test", "evaluation")):
            matched.append(name)
            prof = str(skill.get("proficiency", "")).lower()
            endorsements = int(skill.get("endorsements", 0) or 0)
            duration = int(skill.get("duration_months", 0) or 0)
            score += 0.06
            if prof == "expert":
                score += 0.05
            elif prof == "advanced":
                score += 0.035
            elif prof == "intermediate":
                score += 0.02
            score += min(0.02, endorsements / 200.0)
            score += min(0.02, duration / 240.0)
        elif name_l in lowered:
            matched.append(name)
            score += 0.015
    return max(0.0, min(0.65, score)), matched


def _semantic_score(candidate_text: str, jd: JobDescriptionProfile) -> float:
    tokens = _token_counter(candidate_text)
    score = 0.0
    for term, weight in jd.required_terms.items():
        if term in candidate_text:
            score += weight
    for term, weight in jd.desired_terms.items():
        if term in candidate_text:
            score += 0.8 * weight
    for term, weight in (
        ("embeddings", 3.0),
        ("retrieval", 3.0),
        ("ranking", 2.8),
        ("vector", 1.5),
        ("search", 1.2),
        ("python", 1.0),
        ("production", 1.0),
        ("evaluation", 1.2),
        ("ndcg", 1.6),
        ("mrr", 1.4),
        ("map", 1.0),
        ("llm", 1.0),
        ("fine", 0.8),
    ):
        score += min(tokens.get(term, 0), 3) * weight * 0.1
    return min(3.5, score)


def _disqualifier_penalty(candidate: dict[str, Any], candidate_text: str) -> float:
    score = 0.0
    lowered = candidate_text.lower()
    title = str(candidate.get("profile", {}).get("current_title", "")).lower()
    if any(term in title for term in BAD_BACKGROUND_HINTS):
        score -= 0.35
    if "pure research" in lowered or "academic" in lowered:
        score -= 0.18
    if "langchain" in lowered and not any(term in lowered for term in ("production", "deployed", "evaluation", "retrieval", "ranking")):
        score -= 0.12
    if "cv" in lowered or "robotics" in lowered or "speech" in lowered:
        score -= 0.10
    return max(-0.6, score)


def score_candidate(candidate: dict[str, Any], jd: JobDescriptionProfile) -> tuple[float, dict[str, Any]]:
    candidate_text = flatten_candidate_text(candidate)
    profile = candidate.get("profile", {})
    years = float(profile.get("years_of_experience", 0.0))

    semantic = _semantic_score(candidate_text, jd)
    title_score, title_pattern = _title_score(candidate)
    skills_score, matched_skills = _skill_score(candidate, candidate_text)
    experience_score = _experience_score(years, jd)
    background_score = _product_background_score(candidate)
    location_score = _location_fit(candidate, jd)
    availability_score = _availability_score(candidate)
    plausibility_score = _plausibility_score(candidate)
    penalty_score = _disqualifier_penalty(candidate, candidate_text)

    raw_score = (
        1.85 * semantic
        + 1.45 * title_score
        + 1.45 * skills_score
        + 1.50 * experience_score
        + 0.95 * background_score
        + 0.75 * location_score
        + 0.90 * availability_score
        + 0.85 * plausibility_score
        + penalty_score
    )

    signal = {
        "title_pattern": title_pattern,
        "matched_skills": matched_skills[:6],
        "years": years,
        "semantic": semantic,
        "title_score": title_score,
        "skills_score": skills_score,
        "experience_score": experience_score,
        "background_score": background_score,
        "location_score": location_score,
        "availability_score": availability_score,
        "plausibility_score": plausibility_score,
        "penalty_score": penalty_score,
    }
    return raw_score, signal


def rank_key(candidate: dict[str, Any], raw_score: float) -> tuple[float, int]:
    return raw_score, -_candidate_number(str(candidate.get("candidate_id", "")))


def scaled_score(raw_score: float) -> float:
    return 1.0 / (1.0 + math.exp(-(raw_score - 2.4)))
