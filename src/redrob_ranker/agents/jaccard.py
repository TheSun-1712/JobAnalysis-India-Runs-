from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..job_description import JobDescriptionProfile

class JaccardAgent(BaseAgent):
    def __init__(self, jd: JobDescriptionProfile, corpus_stats: dict[str, Any] | None = None) -> None:
        super().__init__(jd, corpus_stats)
        self.target_skills = {term.lower() for term in self.jd.required_terms.keys()}
        if not self.target_skills:
            self.target_skills = {"python", "sql", "embeddings", "ranking", "retrieval", "vector search", "llm"}

    def score_candidate(self, candidate: dict[str, Any]) -> float:
        skills = {str(s.get("name", "")).strip().lower() for s in candidate.get("skills", []) if s.get("name")}
        if not skills or not self.target_skills:
            return 0.0
            
        intersection = skills.intersection(self.target_skills)
        union = skills.union(self.target_skills)
        
        return len(intersection) / len(union) if union else 0.0
