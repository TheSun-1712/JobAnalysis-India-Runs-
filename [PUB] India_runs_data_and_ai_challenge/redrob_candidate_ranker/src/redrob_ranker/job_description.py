from __future__ import annotations

import re
from dataclasses import dataclass, field


CONSULTING_COMPANIES = {
    "tcs",
    "infosys",
    "wipro",
    "accenture",
    "cognizant",
    "capgemini",
    "hcl",
    "mindtree",
    "lti",
    "persistent",
}


RELEVANT_TITLE_PATTERNS = {
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
    "recommender": 1.0,
}


ROLE_TERMS = {
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
    "mrr@10": 2.0,
}


INDIA_TIER1_MARKERS = {
    "pune",
    "noida",
    "mumbai",
    "hyderabad",
    "bangalore",
    "bengaluru",
    "delhi",
    "delhi ncr",
    "gurugram",
    "gurgaon",
    "chennai",
}


PRODUCT_COMPANY_HINTS = {
    "swiggy",
    "zomato",
    "flipkart",
    "paytm",
    "razorpay",
    "phonepe",
    "inmobi",
    "freshworks",
    "upgrad",
    "haptik",
    "ola",
    "meesho",
    "myntra",
    "amazon",
    "google",
    "meta",
    "microsoft",
    "netflix",
    "uber",
    "airbnb",
    "adobe",
    "servicenow",
    "salesforce",
    "hulu",
    "hooli",
    "acme corp",
}


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
