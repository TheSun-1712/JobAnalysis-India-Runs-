import re
import gzip
import json
import csv
import heapq
import math
from collections import Counter
from dataclasses import dataclass
from typing import List, Dict, Generator, Any, Tuple

import spacy  # type: ignore
import numpy as np
from sklearn.ensemble import IsolationForest  # type: ignore
from rank_bm25 import BM25Okapi  # type: ignore

# ==========================================
# Phase 0: Architecture Data Classes
# ==========================================

@dataclass(slots=True)
class ScoringConfig:
    role_type: str
    seniority: str
    must_have_skills: List[str]
    min_experience: float
    max_experience: float
    domain_keywords: List[str]
    project_signals: List[str]
    disqualifiers: List[str]
    weights: Dict[str, float]

@dataclass(slots=True)
class CandidateProfile:
    id: str
    name: str
    total_experience: float
    skills: List[Dict[str, Any]]
    experience_history: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    location: str
    availability: str
    raw_text: str

# ==========================================
# Phase 1: JD Parser (spaCy + regex)
# ==========================================

def parse_job_description(jd_text: str) -> ScoringConfig:
    """
    Parses experience limits using regex and extracts core technical skills
    using spaCy POS tagging matched against a mock database of technical words.
    """
    min_exp, max_exp = 5.0, 9.0  # default range
    
    # 1. Regex range matching (e.g., "5-8 years", "5 to 8 years")
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*years?", jd_text, re.IGNORECASE)
    if range_match:
        min_exp = float(range_match.group(1))
        max_exp = float(range_match.group(2))
    else:
        # Match single bounds (e.g., "5+ years", "at least 5 years")
        single_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", jd_text, re.IGNORECASE)
        if single_match:
            min_exp = float(single_match.group(1))
            max_exp = min_exp + 4.0

    # 2. Tokenize and extract skills using spaCy POS tagging
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(jd_text)
    
    # Mock technology vocabulary
    TECH_VOCAB = {
        "python", "spacy", "scikit-learn", "numpy", "pandas", "pytorch", 
        "tensorflow", "kubernetes", "aws", "docker", "sql", "git", 
        "java", "next.js", "react", "fastapi", "flask", "c++", "golang", "spark"
    }
    
    must_have_skills = []
    for token in doc:
        if token.pos_ in ("NOUN", "PROPN"):
            text_cleaned = token.text.strip().lower()
            text_cleaned = re.sub(r"[^\w\.\-]", "", text_cleaned) # clean formatting punctuation
            if text_cleaned in TECH_VOCAB and text_cleaned not in must_have_skills:
                must_have_skills.append(text_cleaned)

    # 3. Extract seniority and role context rules
    jd_lower = jd_text.lower()
    seniority = "Mid"
    if "senior" in jd_lower:
        seniority = "Senior"
    elif "lead" in jd_lower:
        seniority = "Lead"
    elif "junior" in jd_lower:
        seniority = "Junior"

    role_type = "Software Engineer"
    if "data" in jd_lower:
        role_type = "Data Engineer"
    elif "backend" in jd_lower:
        role_type = "Backend Engineer"

    # Default matching arrays
    default_domains = ["pipeline", "infrastructure", "scalable", "architecture", "database", "api", "cloud", "matching", "retrieval"]
    domain_keywords = [word for word in default_domains if word in jd_lower]
    project_signals = ["designed", "architected", "optimized", "deployed", "implemented", "built"]
    disqualifiers = ["academic", "internship", "part-time", "consultant"]
    
    default_weights = {
        "semantic": 0.2,
        "skills": 0.3,
        "experience": 0.2,
        "project": 0.3
    }

    return ScoringConfig(
        role_type=role_type,
        seniority=seniority,
        must_have_skills=must_have_skills,
        min_experience=min_exp,
        max_experience=max_exp,
        domain_keywords=domain_keywords,
        project_signals=project_signals,
        disqualifiers=disqualifiers,
        weights=default_weights
    )

# ==========================================
# Phase 2: Ingestion & Streaming Layer
# ==========================================

def stream_candidates(file_path: str) -> Generator[CandidateProfile, None, None]:
    """
    Streams candidate JSON line entries sequentially from a gzipped file.
    Does not load all profiles in memory (O(1) memory footprint per iteration).
    """
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            
            # Key mappings from challenge schema and fallback configurations
            cid = record.get("candidate_id") or record.get("id") or "UNKNOWN_ID"
            profile_data = record.get("profile", {})
            name = record.get("name") or profile_data.get("anonymized_name") or "Anonymized"
            total_exp = float(record.get("total_experience") or profile_data.get("years_of_experience") or 0.0)
            
            # Map candidate skills
            skills = record.get("skills", [])
            
            # Map history logs
            exp_history = record.get("career_history") or record.get("experience_history") or []
            projects = record.get("projects") or []
            
            location = record.get("location") or profile_data.get("location") or ""
            availability = record.get("availability") or str(record.get("redrob_signals", {}).get("notice_period_days", ""))
            
            # Flatten descriptions into unified raw_text block
            text_parts = [
                profile_data.get("headline", ""),
                profile_data.get("summary", "")
            ]
            for exp in exp_history:
                text_parts.append(exp.get("title", ""))
                text_parts.append(exp.get("company", ""))
                text_parts.append(exp.get("description", ""))
            for proj in projects:
                text_parts.append(proj.get("name", ""))
                text_parts.append(proj.get("description", ""))
            
            # Include skill names directly in search index
            for s in skills:
                if isinstance(s, dict):
                    text_parts.append(s.get("name", ""))
                else:
                    text_parts.append(str(s))
            
            raw_text = " ".join([str(p) for p in text_parts if p]).lower()
            
            yield CandidateProfile(
                id=str(cid),
                name=str(name),
                total_experience=total_exp,
                skills=skills,
                experience_history=exp_history,
                projects=projects,
                location=location,
                availability=availability,
                raw_text=raw_text
            )

# ==========================================
# Phase 3: Fake Detection Engine
# ==========================================

class FakeDetector:
    def __init__(self, tech_release_years: Dict[str, int], current_year: int = 2026):
        self.tech_release_years = {k.lower(): v for k, v in tech_release_years.items()}
        self.current_year = current_year
        self.clf: Any = None

    def fit_statistical_model(self, profiles: List[CandidateProfile]):
        """
        Trains IsolationForest outlier detector based on total experience,
        skill catalog length, and project count.
        """
        features = []
        for p in profiles:
            features.append([p.total_experience, len(p.skills), len(p.projects)])
        if features:
            self.clf = IsolationForest(contamination=0.1, random_state=42)
            self.clf.fit(features)

    def check_rules(self, profile: CandidateProfile) -> Tuple[bool, str]:
        """
        Verifies rule-based fraudulent patterns.
        """
        for skill_obj in profile.skills:
            if not isinstance(skill_obj, dict):
                continue
            name = skill_obj.get("name", "").lower()
            duration_months = skill_obj.get("duration_months", 0)
            duration_years = duration_months / 12.0
            
            # Rule 1: Exceeding tech release date constraint
            for tech, release_year in self.tech_release_years.items():
                if tech in name:
                    allowed_years = self.current_year - release_year
                    if duration_years > allowed_years:
                        return True, f"Rule Fraud: '{skill_obj.get('name')}' experience of {duration_years:.1f} years exceeds tech release constraints (released {release_year}, max allowed {allowed_years} years)."
            
            # Rule 2: Skill tenure exceeds candidate overall tenure
            if duration_years > profile.total_experience + 1.0: # 1 year buffer allowance
                return True, f"Rule Fraud: '{skill_obj.get('name')}' tenure of {duration_years:.1f} years exceeds overall experience of {profile.total_experience} years."
                
        return False, ""

    def check_statistical(self, profile: CandidateProfile) -> Tuple[bool, str]:
        """
        Flags outlier candidate profiles using the IsolationForest model.
        """
        if self.clf is None:
            return False, ""
        feats = np.array([[profile.total_experience, len(profile.skills), len(profile.projects)]])
        pred = self.clf.predict(feats)
        if pred[0] == -1:
            return True, "Statistical Fraud: Candidate flagged as an outlier profile by IsolationForest."
        return False, ""

# ==========================================
# Phase 4 & 5: Multi-Dimensional Scorer
# ==========================================

# Synonym lookup table for semantic search expansion
SYNONYM_MAP: Dict[str, List[str]] = {
    "llm": ["large language model", "gpt", "transformer", "llama", "rag", "generative ai"],
    "large language model": ["llm", "gpt", "transformer", "llama", "rag", "generative ai"],
    "rag": ["retrieval augmented generation", "vector search", "embeddings", "llm"],
    "vector database": ["vector db", "milvus", "qdrant", "pinecone", "weaviate", "faiss", "elasticsearch"],
    "vector db": ["vector database", "milvus", "qdrant", "pinecone", "weaviate", "faiss", "elasticsearch"],
    "embeddings": ["vector embeddings", "sentence transformers", "dense retrieval", "semantic search"],
    "nlp": ["natural language processing", "text mining", "spacy", "nltk", "bert", "transformer"],
    "spark": ["pyspark", "apache spark", "hadoop", "mapreduce", "databricks"],
    "sql": ["database", "postgres", "mysql", "oracle", "nosql", "querying"],
    "aws": ["amazon web services", "cloud", "s3", "ec2", "rds", "lambda"],
    "kubernetes": ["k8s", "docker", "containers", "orchestration", "helm"],
    "ml": ["machine learning", "deep learning", "ai", "artificial intelligence", "scikit-learn", "xgboost"],
    "machine learning": ["ml", "deep learning", "ai", "artificial intelligence", "scikit-learn", "xgboost"]
}

class CandidateScorer:
    def __init__(self, config: ScoringConfig, baseline_profiles: List[CandidateProfile]):
        self.config = config
        
        # Tokenize baseline corpus for BM25 background model parameters
        self.corpus_tokens = [p.raw_text.split() for p in baseline_profiles]
        self.bm25 = BM25Okapi(self.corpus_tokens)
        
        # Compile weights array
        self.weights = np.array([
            self.config.weights.get("semantic", 0.2),
            self.config.weights.get("skills", 0.3),
            self.config.weights.get("experience", 0.2),
            self.config.weights.get("project", 0.3)
        ])

    def score(self, profile: CandidateProfile) -> float:
        # Score Dimension 1: Semantic overlap (BM25)
        query = self.config.domain_keywords + self.config.must_have_skills
        query_tokens = [q.lower() for q in query]
        
        # Expand query tokens with synonyms
        expanded_query_tokens: Dict[str, float] = {}
        for q in query_tokens:
            expanded_query_tokens[q] = 1.0  # full weight for exact match
            if q in SYNONYM_MAP:
                for syn in SYNONYM_MAP[q]:
                    for word in syn.split():
                        if word not in expanded_query_tokens:
                            expanded_query_tokens[word] = 0.5  # half weight for synonym matches
                            
        doc_tokens = profile.raw_text.split()
        bm25_score = 0.0
        doc_len = len(doc_tokens)
        if doc_len > 0:
            counts = Counter(doc_tokens)
            for q, weight in expanded_query_tokens.items():
                if q in self.bm25.idf:
                    idf = self.bm25.idf[q]
                    tf = counts[q]
                    k1 = 1.5
                    b = 0.75
                    numerator = tf * (k1 + 1)
                    denominator = tf + k1 * (1.0 - b + b * (doc_len / self.bm25.avgdl))
                    bm25_score += weight * idf * (numerator / denominator)
                    
        # Sigmoid-style compression to bound BM25 in [0, 1] range
        bm25_scaled = bm25_score / (bm25_score + 5.0) if bm25_score > 0 else 0.0

        # Score Dimension 2: Exact skills intersection match
        candidate_skills_lower = set()
        for s in profile.skills:
            if isinstance(s, dict):
                candidate_skills_lower.add(s.get("name", "").lower())
            else:
                candidate_skills_lower.add(str(s).lower())
                
        must_have_lower = {s.lower() for s in self.config.must_have_skills}
        if not must_have_lower:
            skills_score = 1.0
        else:
            intersection = candidate_skills_lower.intersection(must_have_lower)
            skills_score = len(intersection) / len(must_have_lower)

        # Score Dimension 3: Experience Gaussian match
        mid = (self.config.min_experience + self.config.max_experience) / 2.0
        range_val = self.config.max_experience - self.config.min_experience
        sigma = (range_val / 2.0) if range_val > 0 else 2.0
        diff = profile.total_experience - mid
        exp_score = math.exp(-(diff**2) / (2 * (sigma**2)))

        # Score Dimension 4: Project Match (regex verification)
        total_matches = 0
        pattern = re.compile(r"\b(" + "|".join(self.config.project_signals) + r")\b", re.IGNORECASE)
        for proj in profile.projects:
            desc = proj.get("description", "")
            matches = pattern.findall(desc)
            total_matches += len(matches)
        project_score = min(1.0, total_matches / 5.0)

        # Fast Dot-Product scaling
        scores_vector = np.array([bm25_scaled, skills_score, exp_score, project_score])
        final_score = np.dot(self.weights, scores_vector)
        return float(final_score)

# ==========================================
# Phase 6: Heap Ranker & MMR Re-Ranker
# ==========================================

def jaccard_similarity(set1: set, set2: set) -> float:
    if not set1 or not set2:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

def rank_candidates(profile_stream, scorer, detector=None, top_n=20, audit_log=None):
    """
    Ranks candidates using a min-heap structure of size N to keep memory bounded to O(N).
    Applies an MMR similarity pass to scale down duplicate textual candidates.
    """
    if audit_log is None:
        audit_log = []
        
    heap = []
    for profile in profile_stream:
        # Check rule fraud
        if detector is not None:
            is_fake, reason = detector.check_rules(profile)
            if is_fake:
                audit_log.append({
                    "candidate_id": profile.id,
                    "name": profile.name,
                    "reason": reason
                })
                continue
                
            # Check statistical fraud
            is_fake_stat, reason_stat = detector.check_statistical(profile)
            if is_fake_stat:
                audit_log.append({
                    "candidate_id": profile.id,
                    "name": profile.name,
                    "reason": reason_stat
                })
                continue

        score = scorer.score(profile)
        # Use profile.id as a tie-breaker string to avoid dataclass comparisons in the heap
        entry = (score, profile.id, profile)
        
        if len(heap) < top_n:
            heapq.heappush(heap, entry)
        elif score > heap[0][0]:
            heapq.heapreplace(heap, entry)

    # Sort descending
    ranked = []
    while heap:
        ranked.append(heapq.heappop(heap))
    ranked.reverse()

    # MMR Profile Diversity Re-Ranking
    selected = []
    selected_token_sets = []
    for score, cid, profile in ranked:
        tokens = set(profile.raw_text.split())
        
        max_sim = 0.0
        for s_tokens in selected_token_sets:
            sim = jaccard_similarity(tokens, s_tokens)
            if sim > max_sim:
                max_sim = sim
                
        # Scale score down based on similarity (diversity penalty factor = 0.3)
        lambda_const = 0.3
        adjusted_score = score * (1.0 - lambda_const * max_sim)
        selected.append((adjusted_score, score, profile))
        selected_token_sets.append(tokens)

    # Re-sort using MMR adjusted scores
    selected.sort(key=lambda x: x[0], reverse=True)
    return selected

# ==========================================
# Phase 7: reasoning & Pipeline Output
# ==========================================

def write_pipeline_outputs(ranked_candidates, config, audit_log, csv_output_path, audit_output_path):
    # 1. Output Submission CSV
    with open(csv_output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Candidate ID", "Name", "Pipeline Score", "Reasoning"])
        
        for adj_score, orig_score, profile in ranked_candidates:
            # Dynamic reasoning composition
            candidate_skills_lower = set()
            for s in profile.skills:
                if isinstance(s, dict):
                    candidate_skills_lower.add(s.get("name", "").lower())
                else:
                    candidate_skills_lower.add(str(s).lower())
            must_have_lower = {s.lower() for s in config.must_have_skills}
            matched_skills = candidate_skills_lower.intersection(must_have_lower)
            
            exp_status = "falls perfectly within"
            if profile.total_experience < config.min_experience:
                exp_status = "is below"
            elif profile.total_experience > config.max_experience:
                exp_status = "is above"
                
            proj_words = 0
            pattern = re.compile(r"\b(" + "|".join(config.project_signals) + r")\b", re.IGNORECASE)
            for proj in profile.projects:
                desc = proj.get("description", "")
                proj_words += len(pattern.findall(desc))
                
            reason = (
                f"Candidate matched {len(matched_skills)} core skills ({', '.join(list(matched_skills)[:3])}) "
                f"and {exp_status} the target experience bracket of {config.min_experience}-{config.max_experience} years "
                f"with {proj_words} verified deployment project signals."
            )
            writer.writerow([profile.id, profile.name, f"{adj_score:.6f}", reason])
            
    # 2. Output Trace Log
    with open(audit_output_path, "w", encoding="utf-8") as f:
        for entry in audit_log:
            f.write(json.dumps(entry) + "\n")

# ==========================================
# Main Mock Execution Block
# ==========================================

if __name__ == "__main__":
    print("Initializing mock ATS pipeline execution...")
    
    # 1. Mock Job Description
    jd_text = """
    Job Title: Senior Backend and Data Engineer
    Experience: 5-8 years of production software development.
    Required Skills: python, spark, sql, aws.
    Mandate: Own data pipeline scalable structures. Designed and deployed infrastructure.
    """
    
    print("Parsing Job Description...")
    config = parse_job_description(jd_text)
    print(f"Scoring Config created successfully:\n  Seniority: {config.seniority}\n  Skills: {config.must_have_skills}\n  Experience: {config.min_experience}-{config.max_experience} years")

    # 2. Setup mock candidate profiles JSON files structure
    mock_candidates = [
        # Normal Candidate 1 (Good match)
        {
            "candidate_id": "CAND_0000001",
            "profile": {
                "anonymized_name": "Alok Kumar",
                "headline": "Senior Data Engineer | Python & Spark",
                "summary": "Data engineer with 6.5 years experience building reliable systems.",
                "years_of_experience": 6.5,
                "location": "Pune"
            },
            "skills": [
                {"name": "Python", "proficiency": "expert", "duration_months": 78},
                {"name": "Spark", "proficiency": "advanced", "duration_months": 60},
                {"name": "SQL", "proficiency": "expert", "duration_months": 72}
            ],
            "experience_history": [
                {"title": "Data Engineer", "company": "ProductCo", "description": "Designed and deployed massive ETL pipelines."}
            ],
            "projects": [
                {"name": "Migration", "description": "Optimized and scaled the legacy pipelines using spark."}
            ]
        },
        # Normal Candidate 2 (Ideal match)
        {
            "candidate_id": "CAND_0000002",
            "profile": {
                "anonymized_name": "Riya Sen",
                "headline": "Backend Lead | AWS Cloud",
                "summary": "7 years experience. AWS architecture expert.",
                "years_of_experience": 7.0,
                "location": "Noida"
            },
            "skills": [
                {"name": "Python", "proficiency": "expert", "duration_months": 84},
                {"name": "AWS", "proficiency": "expert", "duration_months": 72},
                {"name": "SQL", "proficiency": "advanced", "duration_months": 60}
            ],
            "experience_history": [
                {"title": "Backend Architect", "company": "CloudInc", "description": "Architected microservices and deployed APIs."}
            ],
            "projects": [
                {"name": "App Backend", "description": "Designed and deployed critical cloud structures."}
            ]
        },
        # Fraud candidate (Rule-based: Next.js 14 duration is 6 years, impossible since released in 2023)
        {
            "candidate_id": "CAND_0000003",
            "profile": {
                "anonymized_name": "Fake Candidate",
                "headline": "Full Stack Engineer",
                "summary": "Developer with 10 years experience.",
                "years_of_experience": 10.0,
                "location": "Delhi"
            },
            "skills": [
                {"name": "Next.js 14", "proficiency": "expert", "duration_months": 72}
            ],
            "experience_history": [],
            "projects": []
        },
        # Statistical outlier candidate (45 years experience, 0 projects)
        {
            "candidate_id": "CAND_0000004",
            "profile": {
                "anonymized_name": "Outlier Candidate",
                "headline": "Architect",
                "summary": "Experienced advisor.",
                "years_of_experience": 45.0,
                "location": "Mumbai"
            },
            "skills": [
                {"name": "Python", "proficiency": "intermediate", "duration_months": 12}
            ],
            "experience_history": [],
            "projects": []
        }
    ]

    mock_gz_path = "mock_candidates.jsonl.gz"
    print(f"Generating mock candidates archive at {mock_gz_path}...")
    with gzip.open(mock_gz_path, "wt", encoding="utf-8") as f:
        for c in mock_candidates:
            f.write(json.dumps(c) + "\n")

    # 3. Initialize Fake Detector and fit statistical model on mock baseline
    print("Configuring Fake Detection Engine...")
    tech_releases = {"Next.js 14": 2023, "Python 3.12": 2023}
    detector = FakeDetector(tech_releases, current_year=2026)
    
    # Read normal candidates to build detector baseline
    baseline_stream = stream_candidates(mock_gz_path)
    baseline_profiles = [p for p in baseline_stream if p.id in ("CAND_0000001", "CAND_0000002")]
    detector.fit_statistical_model(baseline_profiles)

    # 4. Initialize Multi-Dimensional Scorer
    print("Configuring Candidate Scorer (BM25 + exact + Gaussian)...")
    scorer = CandidateScorer(config, baseline_profiles)

    # 5. Run the ranking pipeline
    print("Running Streaming Ranking Pipeline...")
    stream = stream_candidates(mock_gz_path)
    audit_log: List[Dict[str, Any]] = []
    ranked_results = rank_candidates(stream, scorer, detector=detector, top_n=20, audit_log=audit_log)

    print("Candidates ranked successfully. Output results:")
    for adj_score, orig_score, p in ranked_results:
        print(f" - {p.name} ({p.id}): MMR Score={adj_score:.4f}, Raw Score={orig_score:.4f}")

    print("\nAudited Fraud candidates:")
    for log in audit_log:
        print(f" - {log['name']} ({log['candidate_id']}): {log['reason']}")

    # 6. Write final outputs
    csv_out = "mock_submission.csv"
    audit_out = "mock_audit.jsonl"
    print(f"\nWriting pipeline outputs to {csv_out} and {audit_out}...")
    write_pipeline_outputs(ranked_results, config, audit_log, csv_out, audit_out)
    print("Done! End-to-end ATS pipeline execution completed flawlessly.")
