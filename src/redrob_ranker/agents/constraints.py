from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..job_description import INDIA_TIER1_MARKERS, JobDescriptionProfile

class ConstraintsAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        profile = candidate.get("profile", {})
        signals = candidate.get("redrob_signals", {})
        
        # 1. Experience score (0.0 to 1.0)
        years = float(profile.get("years_of_experience", 0.0))
        target_min = self.jd.experience_min
        target_max = self.jd.experience_max
        
        if target_min - 1.0 <= years <= target_max + 3.0:
            exp_score = 1.0
        else:
            if years < target_min - 1.0:
                diff = (target_min - 1.0) - years
                exp_score = max(0.0, 1.0 - (diff / 3.0))
            else:
                diff = years - (target_max + 3.0)
                exp_score = max(0.0, 1.0 - (diff / 5.0))

        # 2. Location score (0.0 to 1.0)
        location = f"{profile.get('location', '')} {profile.get('country', '')}".lower()
        has_pref = any(marker in location for marker in INDIA_TIER1_MARKERS)
        is_india = "india" in location
        relocate = bool(signals.get("willing_to_relocate"))
        
        if has_pref or is_india:
            loc_score = 1.0
        elif relocate:
            loc_score = 0.60
        else:
            loc_score = 0.10

        # 3. Work Mode score (0.0 to 1.0)
        pref_mode = str(signals.get("preferred_work_mode", "")).lower()
        jd_mode = self.jd.work_mode
        
        if jd_mode == "hybrid" and pref_mode in {"hybrid", "flexible", "onsite"}:
            mode_score = 1.0
        elif jd_mode == "remote" and pref_mode in {"remote", "flexible"}:
            mode_score = 1.0
        elif jd_mode == "onsite" and pref_mode == "onsite":
            mode_score = 1.0
        else:
            mode_score = 0.50

        return 0.4 * exp_score + 0.35 * loc_score + 0.25 * mode_score
