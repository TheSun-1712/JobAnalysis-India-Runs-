from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..job_description import JobDescriptionProfile

class CompensationAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        signals = candidate.get("redrob_signals", {})
        salary_range = signals.get("expected_salary_range_inr_lpa")
        if not salary_range or not isinstance(salary_range, dict):
            return 0.6
            
        min_expect = float(salary_range.get("min", -1.0))
        if min_expect <= 0.0:
            return 0.6
            
        profile = candidate.get("profile", {})
        years = float(profile.get("years_of_experience", 0.0))
        
        # Calculate an expected benchmark ceiling: base 12 LPA + 6 LPA per year of experience
        benchmark_limit = 12.0 + years * 6.0
        
        if min_expect <= benchmark_limit:
            return 1.0
        else:
            # Exponential/linear decay for over-expectations
            diff = min_expect - benchmark_limit
            score = 1.0 - (diff / 30.0)
            return max(0.1, score)
