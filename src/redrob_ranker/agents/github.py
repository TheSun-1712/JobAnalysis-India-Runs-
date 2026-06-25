from __future__ import annotations
import re
from typing import Any
from .base import BaseAgent
from ..bundle import flatten_candidate_text
from ..job_description import JobDescriptionProfile

GIT_KEYWORDS = {
    "git", "github", "gitlab", "open source", "open-source", "pull request", "pull requests", "fork", "repository", "contribute", "contributing", "contributions"
}

class GithubAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        signals = candidate.get("redrob_signals", {})
        
        # 1. Use the pre-computed github activity score if available (> 0)
        activity_score = float(signals.get("github_activity_score", -1.0))
        score = 0.0
        if activity_score > 0.0:
            # Map activity score (usually out of 100) to agent points (up to 5.0)
            score += min(5.0, activity_score * 0.08)
        elif activity_score == 0.0:
            score += 0.5  # Minimal score for having a profile linked
            
        # 2. Scan job descriptions and summary for git and open-source terms
        cand_text = flatten_candidate_text(candidate)
        words = re.findall(r"[a-z\-]+", cand_text.lower())
        match_count = sum(1 for w in words if w in GIT_KEYWORDS)
        
        score += min(3.0, match_count * 0.3)
        return score
