from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..job_description import JobDescriptionProfile

class StabilityAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        history = candidate.get("career_history", [])
        if not history:
            return 0.0
            
        total_months = 0.0
        num_jobs = len(history)
        short_hops = 0
        
        for job in history:
            duration = self.get_job_duration(job)
            total_months += duration
            
            title = str(job.get("title", "")).lower()
            if duration < 6.0 and duration > 0.0 and "intern" not in title:
                short_hops += 1
                
        avg_tenure = total_months / num_jobs if num_jobs > 0 else 0.0
        
        if avg_tenure >= 36.0:
            score = 1.0
        elif avg_tenure >= 24.0:
            score = 0.85
        elif avg_tenure >= 12.0:
            score = 0.60
        elif avg_tenure >= 6.0:
            score = 0.30
        else:
            score = 0.05
            
        deduction = min(0.40, short_hops * 0.15)
        return max(0.0, score - deduction)
