from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..features import score_candidate

class HeuristicAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        raw_score, _ = score_candidate(candidate, self.jd)
        deduction = self.get_profile_authenticity_deduction(candidate)
        return raw_score - deduction
