from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..job_description import JobDescriptionProfile

class AssessmentAgent(BaseAgent):
    def __init__(self, jd: JobDescriptionProfile, corpus_stats: dict[str, Any] | None = None) -> None:
        super().__init__(jd, corpus_stats)
        self.target_skills = {term.lower() for term in self.jd.required_terms.keys()}
        if not self.target_skills:
            self.target_skills = {"python", "sql", "embeddings", "ranking", "retrieval", "vector search", "llm"}

    def score_candidate(self, candidate: dict[str, Any]) -> float:
        signals = candidate.get("redrob_signals", {})
        scores = signals.get("skill_assessment_scores", {})
        if not scores:
            return 0.0
            
        matched_scores = []
        for skill_name, val in scores.items():
            if skill_name.lower() in self.target_skills:
                matched_scores.append(float(val))
                
        if not matched_scores:
            return 0.0
            
        # Compute average score of matching assessments and map it to a 0-5 scale
        avg_score = sum(matched_scores) / len(matched_scores)
        return min(5.0, avg_score * 0.05)
