from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..job_description import JobDescriptionProfile

ASSOCIATED_SKILLS = {
    "milvus": {"vector search", "pinecone", "qdrant", "weaviate", "faiss", "vector database", "vector db", "hnsw"},
    "pinecone": {"vector search", "milvus", "qdrant", "weaviate", "faiss", "vector database", "vector db", "hnsw"},
    "qdrant": {"vector search", "milvus", "pinecone", "weaviate", "faiss", "vector database", "vector db", "hnsw"},
    "weaviate": {"vector search", "milvus", "pinecone", "qdrant", "faiss", "vector database", "vector db", "hnsw"},
    "faiss": {"vector search", "milvus", "pinecone", "qdrant", "weaviate", "vector database", "vector db", "hnsw"},
    "pyspark": {"spark", "pyspark", "hadoop", "airflow", "data pipeline", "etl", "dbt", "sql"},
    "spark": {"pyspark", "hadoop", "airflow", "data pipeline", "etl", "dbt", "sql"},
    "airflow": {"spark", "pyspark", "data pipeline", "etl", "dbt", "sql"},
    "llm": {"rag", "fine-tuning", "lora", "qlora", "peft", "transformers", "langchain", "prompt engineering", "llamaindex", "embeddings"},
    "ndcg": {"mrr", "map", "ranking", "learning to rank", "ltr", "evaluation", "ab testing", "a/b testing"},
    "mrr": {"ndcg", "map", "ranking", "learning to rank", "ltr", "evaluation", "ab testing", "a/b testing"},
    "map": {"ndcg", "mrr", "ranking", "learning to rank", "ltr", "evaluation", "ab testing", "a/b testing"},
    "ranking": {"ndcg", "mrr", "map", "learning to rank", "ltr", "evaluation", "ab testing", "a/b testing"}
}

class AssociationAgent(BaseAgent):
    def __init__(self, jd: JobDescriptionProfile, corpus_stats: dict[str, Any] | None = None) -> None:
        super().__init__(jd, corpus_stats)
        self.target_skills = {term.lower() for term in self.jd.required_terms.keys()}
        if not self.target_skills:
            self.target_skills = {"python", "sql", "embeddings", "ranking", "retrieval", "vector search", "llm"}

    def score_candidate(self, candidate: dict[str, Any]) -> float:
        skills = {str(s.get("name", "")).strip().lower() for s in candidate.get("skills", []) if s.get("name")}
        if not skills or not self.target_skills:
            return 0.0
            
        score = 0.0
        for target in self.target_skills:
            if target in skills:
                score += 1.0
            else:
                associations = ASSOCIATED_SKILLS.get(target, set())
                matched_associations = skills.intersection(associations)
                if matched_associations:
                    partial_score = len(matched_associations) * 0.20
                    score += min(0.50, partial_score)
                    
        return score
