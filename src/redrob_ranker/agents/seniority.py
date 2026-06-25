from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..job_description import JobDescriptionProfile

class SeniorityAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        history = candidate.get("career_history", [])
        if not history:
            return 0.0
            
        total_score = 0.0
        senior_months = 0.0
        total_months = 0.0
        
        job_levels = []
        chronological_jobs = list(reversed(history))
        
        for job in chronological_jobs:
            title = str(job.get("title", "")).lower()
            duration = self.get_job_duration(job)
            total_months += duration
            
            if any(kw in title for kw in ("principal", "architect", "head", "director", "vice president", "vp")):
                level = 3.0
                senior_months += duration
            elif any(kw in title for kw in ("senior", "sr", "lead", "manager")):
                level = 2.0
                senior_months += duration
            elif any(kw in title for kw in ("intern", "junior", "jr", "associate", "trainee")):
                level = 0.5
            else:
                level = 1.0
                
            job_levels.append(level)
            total_score += duration * level
            
        ratio = senior_months / total_months if total_months > 0 else 0.0
        
        progression_bonus = 0.0
        if len(job_levels) >= 2:
            early_avg = sum(job_levels[:len(job_levels)//2]) / (len(job_levels)//2)
            late_avg = sum(job_levels[len(job_levels)//2:]) / (len(job_levels) - len(job_levels)//2)
            if late_avg > early_avg:
                progression_bonus += 24.0
                
        profile = candidate.get("profile", {})
        curr_title = str(profile.get("current_title", "")).lower()
        if any(kw in curr_title for kw in ("senior", "sr", "lead", "principal", "architect", "head", "director")):
            total_score += 36.0
            
        return total_score + (ratio * 48.0) + progression_bonus
