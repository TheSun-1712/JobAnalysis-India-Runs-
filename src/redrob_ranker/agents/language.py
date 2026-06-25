from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..job_description import JobDescriptionProfile

class LanguageAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        languages = candidate.get("languages", [])
        if not languages:
            return 1.5 # Neutral fallback if list is missing
            
        score = 0.0
        additional_languages = 0
        
        for lang in languages:
            name = str(lang.get("language", "")).strip().lower()
            prof = str(lang.get("proficiency", "")).strip().lower()
            
            if name == "english":
                if any(p in prof for p in ("native", "bilingual", "professional", "fluent", "full")):
                    score += 3.5
                elif any(p in prof for p in ("conversational", "intermediate", "limited")):
                    score += 2.0
                else:
                    score += 0.8
            else:
                additional_languages += 1
                
        # Award extra points for multilingual capability (capped at 1.5)
        score += min(1.5, additional_languages * 0.5)
        
        return score
