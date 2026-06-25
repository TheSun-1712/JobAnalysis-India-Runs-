from __future__ import annotations
import re
from typing import Any
from .base import BaseAgent
from ..bundle import flatten_candidate_text
from ..job_description import JobDescriptionProfile

RESEARCH_KEYWORDS = {
    "publication", "publications", "paper", "papers", "patent", "patents",
    "journal", "journals", "conference", "conferences", "ieee", "springer",
    "arxiv", "thesis", "dissertation", "neurips", "nips", "icml", "cvpr",
    "iclr", "kdd", "acl", "emnlp", "sigir"
}

class ResearchAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        candidate_text = flatten_candidate_text(candidate)
        
        # 1. Count occurrences of research keywords in entire profile
        matched_words = re.findall(r"[a-z]+", candidate_text.lower())
        research_count = sum(1 for word in matched_words if word in RESEARCH_KEYWORDS)
        
        # 2. Check education for Ph.D. or Master's research degrees
        edu_bonus = 0.0
        education = candidate.get("education", [])
        for edu in education:
            degree = str(edu.get("degree", "")).lower()
            if any(kw in degree for kw in ("phd", "ph.d", "doctorate", "doctor")):
                edu_bonus += 5.0
            elif any(kw in degree for kw in ("master", "ms", "m.s", "m.tech", "msc")):
                edu_bonus += 1.5
                
        # 3. Check for explicitly research-focused job titles
        history = candidate.get("career_history", [])
        title_bonus = 0.0
        for job in history:
            title = str(job.get("title", "")).lower()
            if "research" in title:
                title_bonus += 2.0
                
        return min(10.0, (research_count * 0.4) + edu_bonus + title_bonus)
