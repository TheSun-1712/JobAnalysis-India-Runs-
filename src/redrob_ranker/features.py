from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .bundle import flatten_candidate_text
from .config import (
    AVAIL_SETTINGS,
    BAD_BACKGROUND_HINTS,
    CONSULTING_COMPANIES,
    DISQ_PENALTIES,
    EXP_SETTINGS,
    INDIA_TIER1_MARKERS,
    LOC_SETTINGS,
    PLAUS_SETTINGS,
    PRODUCT_BG_SETTINGS,
    PRODUCT_COMPANY_HINTS,
    RELEVANT_SKILLS,
    RELEVANT_TITLE_PATTERNS,
    SIGMOID_CENTER,
    SKILL_SCORING_SETTINGS,
    TITLE_NORMALIZATION,
    WEIGHTS,
)
from .job_description import JobDescriptionProfile


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


# Module-level performance optimization constants
TOKEN_RE = re.compile(r"[a-z0-9\+\#\-/']+")

SKILL_SUBSTRINGS = (
    "python", "sql", "spark", "airflow", "llm", "embedding", "retrieval", 
    "ranking", "vector", "milvus", "faiss", "qdrant", "weaviate", "pinecone", 
    "ndcg", "mrr", "map", "ab test", "evaluation"
)

SEMANTIC_TERM_WEIGHTS = (
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
)

TECHNICAL_TITLE_HINTS = ("engineer", "scientist", "analyst", "developer", "architect")

HYBRID_MODES = {"hybrid", "flexible", "onsite"}
REMOTE_MODES = {"remote", "flexible"}


def _token_counter(text: str) -> Counter[str]:
    return Counter(TOKEN_RE.findall(text.lower()))


def _gaussian(value: float, center: float, sigma: float) -> float:
    if sigma <= 0:
        return 0.0
    return math.exp(-((value - center) ** 2) / (2.0 * sigma * sigma))


# ============================================================================
# Evaluator Interface & Implementations (Micro-Agents / Components)
# ============================================================================

class SemanticEvaluator:
    def evaluate(self, candidate: dict[str, Any], jd: JobDescriptionProfile, candidate_text: str) -> float:
        tokens = _token_counter(candidate_text)
        score = 0.0
        for term, weight in jd.required_terms.items():
            if term in candidate_text:
                score += weight
        for term, weight in jd.desired_terms.items():
            if term in candidate_text:
                score += 0.8 * weight
        for term, weight in SEMANTIC_TERM_WEIGHTS:
            score += min(tokens.get(term, 0), 3) * weight * 0.1
        return min(3.5, score)


class TitleEvaluator:
    def evaluate(self, candidate: dict[str, Any], jd: JobDescriptionProfile, candidate_text: str) -> tuple[float, str]:
        title = str(candidate.get("profile", {}).get("current_title", "")).lower()
        normalized = TITLE_NORMALIZATION.get(title, title)
        for pattern, score in RELEVANT_TITLE_PATTERNS.items():
            if pattern in normalized:
                return score, pattern
        return 0.0, ""


class SkillsEvaluator:
    def evaluate(self, candidate: dict[str, Any], jd: JobDescriptionProfile, candidate_text: str) -> tuple[float, list[str]]:
        skills = candidate.get("skills", [])
        matched: list[str] = []
        score = 0.0
        lowered = candidate_text.lower()
        
        cfg = SKILL_SCORING_SETTINGS
        base_skill = cfg.get("base_skill_bonus", 0.06)
        prof_expert = cfg.get("proficiency_expert_bonus", 0.05)
        prof_advanced = cfg.get("proficiency_advanced_bonus", 0.035)
        prof_intermediate = cfg.get("proficiency_intermediate_bonus", 0.02)
        end_factor = cfg.get("endorsements_factor", 200.0)
        end_cap = cfg.get("endorsements_cap", 0.02)
        dur_factor = cfg.get("duration_factor", 240.0)
        dur_cap = cfg.get("duration_cap", 0.02)
        non_prim = cfg.get("non_primary_matching_bonus", 0.015)
        
        for skill in skills:
            name = str(skill.get("name", "")).strip()
            if not name:
                continue
            name_l = name.lower()
            if name_l in RELEVANT_SKILLS or any(
                token in name_l for token in SKILL_SUBSTRINGS
            ):
                matched.append(name)
                prof = str(skill.get("proficiency", "")).lower()
                endorsements = int(skill.get("endorsements", 0) or 0)
                duration = int(skill.get("duration_months", 0) or 0)
                score += base_skill
                if prof == "expert":
                    score += prof_expert
                elif prof == "advanced":
                    score += prof_advanced
                elif prof == "intermediate":
                    score += prof_intermediate
                score += min(end_cap, endorsements / end_factor)
                score += min(dur_cap, duration / dur_factor)
            elif name_l in lowered:
                matched.append(name)
                score += non_prim
                
        return max(cfg.get("min_score", 0.0), min(cfg.get("max_score", 0.65), score)), matched


class ExperienceEvaluator:
    def evaluate(self, candidate: dict[str, Any], jd: JobDescriptionProfile, candidate_text: str) -> float:
        profile = candidate.get("profile", {})
        years = float(profile.get("years_of_experience", 0.0))
        center = jd.target_experience
        
        cfg = EXP_SETTINGS
        base = _gaussian(years, center, cfg.get("sigma", 2.1))
        
        if years < jd.experience_min:
            base *= cfg.get("min_experience_penalty_factor", 0.55)
        elif years > jd.experience_max + cfg.get("max_experience_buffer", 3.0):
            base *= cfg.get("max_experience_penalty_factor", 0.70)
            
        return base


class BackgroundEvaluator:
    def evaluate(self, candidate: dict[str, Any], jd: JobDescriptionProfile, candidate_text: str) -> float:
        history = candidate.get("career_history", [])
        if not history:
            return 0.0
            
        product_hits = 0
        consulting_hits = 0
        technical_hits = 0
        
        cfg = PRODUCT_BG_SETTINGS
        
        for item in history:
            company = str(item.get("company", "")).lower()
            title = str(item.get("title", "")).lower()
            text = f"{company} {title} {item.get('industry', '')}".lower()
            if any(hint in text for hint in PRODUCT_COMPANY_HINTS):
                product_hits += 1
            if any(hint in text for hint in CONSULTING_COMPANIES):
                consulting_hits += 1
            if any(hint in title for hint in TECHNICAL_TITLE_HINTS):
                technical_hits += 1
                
        score = (
            cfg.get("product_hit_bonus", 0.15) * product_hits
            + cfg.get("technical_hit_bonus", 0.10) * technical_hits
            - abs(cfg.get("consulting_hit_penalty", -0.12)) * consulting_hits
        )
        if consulting_hits and product_hits == 0:
            score -= abs(cfg.get("pure_consulting_penalty", -0.25))
            
        return max(cfg.get("min_score", -0.4), min(cfg.get("max_score", 0.45), score))


class LocationEvaluator:
    def evaluate(self, candidate: dict[str, Any], jd: JobDescriptionProfile, candidate_text: str) -> float:
        profile = candidate.get("profile", {})
        signals = candidate.get("redrob_signals", {})
        location = f"{profile.get('location', '')} {profile.get('country', '')}".lower()
        preferred = any(marker in location for marker in INDIA_TIER1_MARKERS)
        india = "india" in location
        relocate = bool(signals.get("willing_to_relocate"))
        mode = str(signals.get("preferred_work_mode", "")).lower()
        
        cfg = LOC_SETTINGS
        bonus = 0.0
        if preferred or india:
            bonus += cfg.get("tier1_bonus", 0.18)
        elif relocate:
            bonus += cfg.get("relocate_bonus", 0.06)
        else:
            bonus += cfg.get("other_penalty", -0.12)
            
        match_bonus = cfg.get("match_bonus", 0.08)
        if jd.work_mode == "hybrid" and mode in HYBRID_MODES:
            bonus += match_bonus
        elif jd.work_mode == "remote" and mode in REMOTE_MODES:
            bonus += match_bonus
        elif jd.work_mode == "onsite" and mode == "onsite":
            bonus += match_bonus
            
        return max(cfg.get("min_score", -0.3), min(cfg.get("max_score", 0.32), bonus))


class AvailabilityEvaluator:
    def evaluate(self, candidate: dict[str, Any], jd: JobDescriptionProfile, candidate_text: str) -> float:
        signals = candidate.get("redrob_signals", {})
        profile = candidate.get("profile", {})
        score = 0.0
        cfg = AVAIL_SETTINGS
        
        if signals.get("open_to_work_flag"):
            score += cfg.get("open_to_work_bonus", 0.18)
            
        response_rate = float(signals.get("recruiter_response_rate", 0.0))
        score += min(cfg.get("response_rate_cap", 0.12), response_rate * cfg.get("response_rate_factor", 0.16))
        
        avg_resp_hours = float(signals.get("avg_response_time_hours", 999.0))
        max_resp_limit = cfg.get("avg_response_time_max", 240.0)
        time_factor = cfg.get("avg_response_time_factor", 0.08)
        score += min(cfg.get("avg_response_time_cap", 0.08), max(0.0, 1.0 - avg_resp_hours / max_resp_limit) * time_factor)
        
        completion_rate = float(signals.get("interview_completion_rate", 0.0))
        score += min(cfg.get("interview_completion_cap", 0.06), completion_rate * cfg.get("interview_completion_factor", 0.06))
        
        notice = float(signals.get("notice_period_days", 180))
        if notice <= 30:
            score += cfg.get("notice_period_30_bonus", 0.12)
        elif notice <= 60:
            score += cfg.get("notice_period_60_bonus", 0.05)
        elif notice <= 90:
            score += cfg.get("notice_period_90_bonus", 0.0)
        else:
            score += cfg.get("notice_period_long_penalty", -0.08)
            
        if signals.get("verified_email"):
            score += cfg.get("verified_email_bonus", 0.04)
        if signals.get("verified_phone"):
            score += cfg.get("verified_phone_bonus", 0.04)
        if signals.get("linkedin_connected"):
            score += cfg.get("linkedin_connected_bonus", 0.02)
        if profile.get("years_of_experience", 0) >= 5:
            score += cfg.get("senior_experience_bonus", 0.02)
            
        return max(cfg.get("min_score", -0.15), min(cfg.get("max_score", 0.55), score))


class PlausibilityEvaluator:
    def evaluate(self, candidate: dict[str, Any], jd: JobDescriptionProfile, candidate_text: str) -> float:
        profile = candidate.get("profile", {})
        history = candidate.get("career_history", [])
        signals = candidate.get("redrob_signals", {})
        years = float(profile.get("years_of_experience", 0.0))
        career_years = sum(float(item.get("duration_months", 0)) for item in history) / 12.0
        delta = abs(career_years - years)
        
        cfg = PLAUS_SETTINGS
        score = cfg.get("base_score", 0.18)
        
        if delta <= 1.0:
            score += cfg.get("delta_1_bonus", 0.16)
        elif delta <= 2.5:
            score += cfg.get("delta_2_5_bonus", 0.08)
        elif delta <= 4.0:
            score += cfg.get("delta_4_penalty", -0.02)
        else:
            score += cfg.get("delta_long_penalty", -0.14)
            
        completeness = float(signals.get("profile_completeness_score", 0.0))
        score += min(cfg.get("completeness_cap", 0.08), completeness / cfg.get("completeness_factor", 200.0))
        
        if float(signals.get("github_activity_score", -1.0)) >= 0:
            score += cfg.get("github_bonus", 0.03)
        if float(signals.get("search_appearance_30d", 0)) > 0:
            score += cfg.get("search_appearance_bonus", 0.02)
        if float(signals.get("saved_by_recruiters_30d", 0)) > 0:
            score += cfg.get("saved_by_recruiters_bonus", 0.02)
            
        return max(cfg.get("min_score", -0.2), min(cfg.get("max_score", 0.45), score))


class PenaltyEvaluator:
    def evaluate(self, candidate: dict[str, Any], jd: JobDescriptionProfile, candidate_text: str) -> float:
        score = 0.0
        lowered = candidate_text.lower()
        title = str(candidate.get("profile", {}).get("current_title", "")).lower()
        
        cfg = DISQ_PENALTIES
        
        if any(term in title for term in BAD_BACKGROUND_HINTS):
            score += cfg.get("bad_title_penalty", -0.35)
        if "pure research" in lowered or "academic" in lowered:
            score += cfg.get("pure_research_penalty", -0.18)
        if "langchain" in lowered and not any(
            term in lowered for term in ("production", "deployed", "evaluation", "retrieval", "ranking")
        ):
            score += cfg.get("unproductive_langchain_penalty", -0.12)
        if "cv" in lowered or "robotics" in lowered or "speech" in lowered:
            score += cfg.get("alternate_fields_penalty", -0.10)
            
        return max(cfg.get("min_score", -0.6), score)


# ============================================================================
# Main Entrypoints
# ============================================================================

# Pre-instantiated micro-agents / components
EVALUATORS = {
    "semantic": SemanticEvaluator(),
    "title": TitleEvaluator(),
    "skills": SkillsEvaluator(),
    "experience": ExperienceEvaluator(),
    "background": BackgroundEvaluator(),
    "location": LocationEvaluator(),
    "availability": AvailabilityEvaluator(),
    "plausibility": PlausibilityEvaluator(),
    "penalty": PenaltyEvaluator(),
}


def score_candidate(candidate: dict[str, Any], jd: JobDescriptionProfile) -> tuple[float, dict[str, Any]]:
    candidate_text = flatten_candidate_text(candidate)
    profile = candidate.get("profile", {})
    years = float(profile.get("years_of_experience", 0.0))

    # Evaluate using the modular agents
    semantic = EVALUATORS["semantic"].evaluate(candidate, jd, candidate_text)
    title_score, title_pattern = EVALUATORS["title"].evaluate(candidate, jd, candidate_text)
    skills_score, matched_skills = EVALUATORS["skills"].evaluate(candidate, jd, candidate_text)
    experience_score = EVALUATORS["experience"].evaluate(candidate, jd, candidate_text)
    background_score = EVALUATORS["background"].evaluate(candidate, jd, candidate_text)
    location_score = EVALUATORS["location"].evaluate(candidate, jd, candidate_text)
    availability_score = EVALUATORS["availability"].evaluate(candidate, jd, candidate_text)
    plausibility_score = EVALUATORS["plausibility"].evaluate(candidate, jd, candidate_text)
    penalty_score = EVALUATORS["penalty"].evaluate(candidate, jd, candidate_text)

    # Compute raw score based on config weights
    raw_score = (
        WEIGHTS["semantic"] * semantic
        + WEIGHTS["title_score"] * title_score
        + WEIGHTS["skills_score"] * skills_score
        + WEIGHTS["experience_score"] * experience_score
        + WEIGHTS["background_score"] * background_score
        + WEIGHTS["location_score"] * location_score
        + WEIGHTS["availability_score"] * availability_score
        + WEIGHTS["plausibility_score"] * plausibility_score
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
    return 1.0 / (1.0 + math.exp(-(raw_score - SIGMOID_CENTER)))
