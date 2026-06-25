from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..job_description import JobDescriptionProfile

class EngagementAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        signals = candidate.get("redrob_signals", {})
        
        # 1. Profile views in last 30 days
        views = float(signals.get("profile_views_received_30d", 0.0) or 0.0)
        views_score = min(1.5, views * 0.08)
        
        # 2. Recruiter saves
        saves = float(signals.get("saved_by_recruiters_30d", 0.0) or 0.0)
        saves_score = min(2.0, saves * 0.20)
        
        # 3. Connection count
        connections = float(signals.get("connection_count", 0.0) or 0.0)
        conn_score = min(1.0, connections / 500.0)
        
        # 4. Interview completion rate
        interview_rate = float(signals.get("interview_completion_rate", 0.0) or 0.0)
        interview_score = min(1.5, interview_rate * 1.5) if interview_rate > 0.0 else 0.0
        
        return views_score + saves_score + conn_score + interview_score
