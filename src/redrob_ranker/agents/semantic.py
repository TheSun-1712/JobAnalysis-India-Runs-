from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..bundle import flatten_candidate_text
from ..job_description import JobDescriptionProfile

CONCEPT_EXPANSIONS = {
    "llm": {"llm", "llms", "large language model", "large language models", "gpt", "gpt-4", "gpt-3", "llama", "claude", "mistral", "gemini", "transformer", "transformers", "attention mechanism", "prompt engineering", "langchain", "llamaindex", "rag", "retrieval augmented generation", "fine-tuning", "lora", "qlora", "peft", "parameter-efficient"},
    "vector search": {"vector search", "vector database", "vector db", "vector databases", "embeddings", "embedding", "milvus", "pinecone", "qdrant", "weaviate", "faiss", "annoy", "hnsw", "nearest neighbor", "semantic search", "dense retrieval"},
    "ranking": {"ranking", "ranker", "learning to rank", "ltr", "ndcg", "mrr", "map", "reciprocal rank", "reranking", "reranker", "cross-encoder", "bi-encoder", "two-stage retrieval"},
    "evaluation": {"evaluation", "eval", "evals", "benchmark", "benchmarks", "offline evaluation", "ab testing", "a/b testing", "ndcg@10", "mrr@10", "accuracy", "precision", "recall", "f1 score"},
    "data engineering": {"data engineer", "data engineering", "spark", "pyspark", "airflow", "dbt", "etl", "data pipeline", "data pipelines", "kafka", "hadoop", "hive", "sql", "clickhouse", "snowflake"},
    "backend development": {"backend", "python", "fastapi", "django", "flask", "flask-restful", "rest api", "grpc", "microservices", "docker", "kubernetes", "scaling", "production", "latency", "throughput"}
}

class SemanticAgent(BaseAgent):
    def __init__(self, jd: JobDescriptionProfile, corpus_stats: dict[str, Any] | None = None) -> None:
        super().__init__(jd, corpus_stats)
        self.active_concepts: dict[str, float] = {}
        jd_text = str(self.corpus_stats.get("jd_text", "")).lower()
        
        for name, synonyms in CONCEPT_EXPANSIONS.items():
            match_count = sum(1 for syn in synonyms if syn in jd_text)
            if match_count > 0:
                self.active_concepts[name] = max(1.0, float(match_count))

    def score_candidate(self, candidate: dict[str, Any]) -> float:
        if not self.active_concepts:
            return 0.0
            
        candidate_text = flatten_candidate_text(candidate)
        score = 0.0
        
        for name, weight in self.active_concepts.items():
            synonyms = CONCEPT_EXPANSIONS[name]
            matched_syns = sum(1 for syn in synonyms if syn in candidate_text)
            
            if matched_syns > 0:
                # Soft match scoring: baseline 0.6 for matching at least one synonym, 
                # up to 1.0 if they match multiple synonyms (max 3)
                overlap_ratio = min(3.0, float(matched_syns)) / 3.0
                score += weight * (0.6 + 0.4 * overlap_ratio)
                
        # Add minor soft-skills / leadership bonus as tie-breaker
        soft_skills = {"mentoring", "mentor", "mentored", "leadership", "leader", "led", "collaboration", "collaborate", "collaborated", "agile", "scrum", "cross-functional", "communication", "stakeholders"}
        matched_soft = sum(1 for word in soft_skills if word in candidate_text)
        soft_bonus = min(0.35, matched_soft * 0.05)
        
        return score + soft_bonus
