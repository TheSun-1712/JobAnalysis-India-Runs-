from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Resolve configuration file path
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        _config = json.load(f)
except Exception:
    _config = {}


def get_setting(path: str, default: Any = None) -> Any:
    """Helper to fetch nested keys in config dict (e.g. 'weights.semantic')"""
    parts = path.split(".")
    curr = _config
    for part in parts:
        if isinstance(curr, dict) and part in curr:
            curr = curr[part]
        else:
            return default
    return curr


# Exposed configuration properties with robust fallbacks
WEIGHTS = get_setting("weights", {
    "semantic": 1.85,
    "title_score": 1.45,
    "skills_score": 1.45,
    "experience_score": 1.50,
    "background_score": 0.95,
    "location_score": 0.75,
    "availability_score": 0.90,
    "plausibility_score": 0.85
})

SIGMOID_CENTER = get_setting("sigmoid_center", 2.4)

EXP_SETTINGS = get_setting("experience_settings", {
    "sigma": 2.1,
    "min_experience_penalty_factor": 0.55,
    "max_experience_penalty_factor": 0.70,
    "max_experience_buffer": 3.0
})

AVAIL_SETTINGS = get_setting("availability_settings", {
    "open_to_work_bonus": 0.18,
    "response_rate_factor": 0.16,
    "response_rate_cap": 0.12,
    "avg_response_time_max": 240.0,
    "avg_response_time_factor": 0.08,
    "avg_response_time_cap": 0.08,
    "interview_completion_factor": 0.06,
    "interview_completion_cap": 0.06,
    "notice_period_30_bonus": 0.12,
    "notice_period_60_bonus": 0.05,
    "notice_period_90_bonus": 0.0,
    "notice_period_long_penalty": -0.08,
    "verified_email_bonus": 0.04,
    "verified_phone_bonus": 0.04,
    "linkedin_connected_bonus": 0.02,
    "senior_experience_bonus": 0.02,
    "min_score": -0.15,
    "max_score": 0.55
})

PLAUS_SETTINGS = get_setting("plausibility_settings", {
    "base_score": 0.18,
    "delta_1_bonus": 0.16,
    "delta_2_5_bonus": 0.08,
    "delta_4_penalty": -0.02,
    "delta_long_penalty": -0.14,
    "completeness_factor": 200.0,
    "completeness_cap": 0.08,
    "github_bonus": 0.03,
    "search_appearance_bonus": 0.02,
    "saved_by_recruiters_bonus": 0.02,
    "min_score": -0.2,
    "max_score": 0.45
})

LOC_SETTINGS = get_setting("location_settings", {
    "tier1_bonus": 0.18,
    "relocate_bonus": 0.06,
    "other_penalty": -0.12,
    "match_bonus": 0.08,
    "min_score": -0.3,
    "max_score": 0.32
})

PRODUCT_BG_SETTINGS = get_setting("product_background_settings", {
    "product_hit_bonus": 0.15,
    "technical_hit_bonus": 0.10,
    "consulting_hit_penalty": -0.12,
    "pure_consulting_penalty": -0.25,
    "min_score": -0.4,
    "max_score": 0.45
})

SKILL_SCORING_SETTINGS = get_setting("skill_scoring_settings", {
    "base_skill_bonus": 0.06,
    "proficiency_expert_bonus": 0.05,
    "proficiency_advanced_bonus": 0.035,
    "proficiency_intermediate_bonus": 0.02,
    "endorsements_factor": 200.0,
    "endorsements_cap": 0.02,
    "duration_factor": 240.0,
    "duration_cap": 0.02,
    "non_primary_matching_bonus": 0.015,
    "min_score": 0.0,
    "max_score": 0.65
})

DISQ_PENALTIES = get_setting("disqualifier_penalties", {
    "bad_title_penalty": -0.35,
    "pure_research_penalty": -0.18,
    "unproductive_langchain_penalty": -0.12,
    "alternate_fields_penalty": -0.10,
    "min_score": -0.6
})

TITLE_NORMALIZATION = get_setting("title_normalization", {
    "ai specialist": "ai engineer",
    "machine learning engineer": "ml engineer",
    "recommendation systems engineer": "recommendation engineer",
    "ai research engineer": "ai engineer",
    "senior machine learning engineer": "ml engineer",
    "senior data engineer": "data engineer",
    "senior software engineer": "software engineer",
    "full stack developer": "software engineer"
})

RELEVANT_SKILLS = set(get_setting("relevant_skills", [
    "python", "sql", "spark", "airflow", "dbt", "pyspark", "nlp", "llm", "llms",
    "embeddings", "retrieval", "ranking", "vector search", "vector database",
    "milvus", "pinecone", "weaviate", "qdrant", "faiss", "elasticsearch",
    "opensearch", "learning to rank", "lora", "qlora", "peft", "evaluation",
    "ndcg", "mrr", "map", "ab testing", "a/b testing", "recommender systems",
    "recommendation systems", "fine-tuning llms", "bentoml"
]))

BAD_BACKGROUND_HINTS = set(get_setting("bad_background_hints", [
    "consultant", "consulting", "sales", "recruiter", "teacher", "writer",
    "designer", "accountant", "hr manager", "customer support", "operations manager"
]))

CONSULTING_COMPANIES = set(get_setting("consulting_companies", [
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", "hcl",
    "mindtree", "lti", "persistent"
]))

RELEVANT_TITLE_PATTERNS = get_setting("relevant_title_patterns", {
    "ai engineer": 1.0,
    "ml engineer": 1.0,
    "machine learning engineer": 1.0,
    "recommendation systems engineer": 1.0,
    "ai specialist": 0.9,
    "ai research engineer": 0.95,
    "data engineer": 0.72,
    "backend engineer": 0.68,
    "software engineer": 0.60,
    "senior software engineer": 0.64,
    "senior data engineer": 0.76,
    "applied scientist": 0.96,
    "search engineer": 1.0,
    "ranking engineer": 1.0,
    "recommender": 1.0
})

ROLE_TERMS = get_setting("role_terms", {
    "embeddings": 3.0,
    "retrieval": 3.0,
    "ranking": 2.8,
    "vector search": 2.7,
    "vector database": 2.6,
    "vector db": 2.4,
    "milvus": 2.6,
    "pinecone": 2.5,
    "weaviate": 2.5,
    "qdrant": 2.5,
    "faiss": 2.5,
    "elasticsearch": 2.2,
    "opensearch": 2.2,
    "search": 1.6,
    "recommendation": 2.2,
    "recommender": 2.2,
    "learning to rank": 2.8,
    "ltr": 2.4,
    "ndcg": 2.7,
    "mrr": 2.5,
    "map": 2.0,
    "ab test": 1.8,
    "a/b": 1.8,
    "offline evaluation": 2.2,
    "python": 1.4,
    "production": 1.4,
    "fine-tuning": 1.6,
    "lora": 1.5,
    "qlora": 1.5,
    "peft": 1.5,
    "llm": 1.2,
    "open source": 0.9,
    "hybrid search": 2.2,
    "hybrid": 0.6,
    "retriever": 2.3,
    "ranker": 2.3,
    "evaluation": 1.4,
    "ndcg@10": 2.0,
    "mrr@10": 2.0
})

INDIA_TIER1_MARKERS = set(get_setting("india_tier1_markers", [
    "pune", "noida", "mumbai", "hyderabad", "bangalore", "bengaluru", "delhi",
    "delhi ncr", "gurugram", "gurgaon", "chennai"
]))

PRODUCT_COMPANY_HINTS = set(get_setting("product_company_hints", [
    "swiggy", "zomato", "flipkart", "paytm", "razorpay", "phonepe", "inmobi",
    "freshworks", "upgrad", "haptik", "ola", "meesho", "myntra", "amazon",
    "google", "meta", "microsoft", "netflix", "uber", "airbnb", "adobe",
    "servicenow", "salesforce", "hulu", "hooli", "acme corp"
]))
