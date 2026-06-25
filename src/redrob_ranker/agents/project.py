from __future__ import annotations
import re
from typing import Any
from .base import BaseAgent
from ..bundle import flatten_candidate_text
from ..job_description import JobDescriptionProfile

PROJECT_KEYWORDS = {
    "kaggle", "side project", "side-project", "personal project", "hobby project", 
    "hackathon", "hackathons", "hobby", "open-source repo", "github repo", 
    "repository", "self-taught", "self-directed", "portfolio", "side-hustle"
}

class ProjectAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        cand_text = flatten_candidate_text(candidate)
        words = re.findall(r"[a-z\-]+", cand_text.lower())
        
        # Count keywords indicating personal coding activities
        match_count = sum(1 for w in words if w in PROJECT_KEYWORDS)
        
        # Give higher weight to Kaggle mentions specifically
        kaggle_count = len(re.findall(r"\bkaggle\b", cand_text.lower()))
        
        score = (match_count * 0.40) + (kaggle_count * 1.20)
        return min(5.0, score)
