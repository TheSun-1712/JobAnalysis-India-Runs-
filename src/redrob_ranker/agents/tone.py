from __future__ import annotations
import re
from typing import Any
from .base import BaseAgent
from ..job_description import JobDescriptionProfile

PRO_KEYWORDS = {
    "experience", "skills", "proven", "successful", "built", "designed", "scaled", 
    "led", "seeking", "passionate", "engineered", "delivered", "implemented", "optimized"
}

BUZZWORDS = {
    "guru", "ninja", "rockstar", "world-class", "disruptive", "synergy", "think outside the box"
}

class ToneAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        profile = candidate.get("profile", {})
        summary = str(profile.get("summary", "")).strip()
        if not summary:
            return 0.0
            
        words = re.findall(r"[a-z']+", summary.lower())
        word_count = len(words)
        
        # 1. Word count scoring (bell curve: optimal is between 40 and 120 words)
        if 40 <= word_count <= 120:
            count_score = 2.0
        elif 15 <= word_count < 40:
            count_score = 1.0
        elif 120 < word_count <= 200:
            count_score = 1.2
        else:
            count_score = 0.2
            
        # 2. Key verbs and professional vocabulary
        pro_matches = sum(1 for w in words if w in PRO_KEYWORDS)
        vocab_score = min(2.0, pro_matches * 0.40)
        
        # 3. Buzzwords penalty
        buzz_matches = sum(1 for w in words if w in BUZZWORDS)
        buzz_penalty = min(1.0, buzz_matches * 0.30)
        
        # 4. Check for bullet points or structural breaks in text
        structure_score = 0.0
        if "\n" in summary or "•" in summary or "|" in summary or "-" in summary:
            structure_score += 1.0
            
        return max(0.1, count_score + vocab_score + structure_score - buzz_penalty)
