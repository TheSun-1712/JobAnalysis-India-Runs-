from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
import heapq
import re
from ..job_description import JobDescriptionProfile

class BaseAgent(ABC):
    def __init__(self, jd: JobDescriptionProfile, corpus_stats: dict[str, Any] | None = None) -> None:
        self.jd = jd
        self.corpus_stats = corpus_stats or {}
        # Stores (score, counter, candidate_dict)
        self.heap: list[tuple[float, int, dict[str, Any]]] = []
        self._counter = 0

    @abstractmethod
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        """Score a single candidate record."""
        pass

    def update(self, candidate: dict[str, Any], max_size: int = 500) -> None:
        """Evaluate a candidate and update the top candidates heap."""
        score = self.score_candidate(candidate)
        self._counter += 1
        entry = (score, self._counter, candidate)
        if len(self.heap) < max_size:
            heapq.heappush(self.heap, entry)
        elif score > self.heap[0][0]:
            heapq.heapreplace(self.heap, entry)

    def get_top_rankings(self) -> list[tuple[float, dict[str, Any]]]:
        """Return the sorted top candidates from this agent, highest score first."""
        def sorting_key(entry: tuple[float, int, dict[str, Any]]) -> tuple[float, float, int]:
            score, _, cand = entry
            profile = cand.get("profile", {})
            years = -float(profile.get("years_of_experience", 0.0))
            cid = cand.get("candidate_id", "")
            try:
                cid_num = int(str(cid).split("_")[-1])
            except Exception:
                cid_num = 10**9
            return -score, years, cid_num

        sorted_entries = sorted(self.heap, key=sorting_key)
        return [(entry[0], entry[2]) for entry in sorted_entries]

    def get_job_duration(self, job: dict[str, Any]) -> float:
        """Helper to get job duration in months, fallback to parsing start/end dates."""
        duration = float(job.get("duration_months", 0.0) or 0.0)
        if duration > 0.0:
            return duration

        start_s = job.get("start_date")
        if not start_s:
            return 12.0  # Fallback: 1 year default

        try:
            start_dt = datetime.strptime(str(start_s).strip(), "%Y-%m-%d")
            end_s = job.get("end_date")
            
            if not end_s or job.get("is_current"):
                # Use current local simulation year (June 2026)
                end_dt = datetime(2026, 6, 25)
            else:
                end_dt = datetime.strptime(str(end_s).strip(), "%Y-%m-%d")
                
            months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
            return max(1.0, float(months))
        except Exception:
            return 12.0

    def get_profile_authenticity_deduction(self, candidate: dict[str, Any]) -> float:
        """Helper to compute profile authenticity deductions for placeholder/fake contact info."""
        profile = candidate.get("profile", {})
        signals = candidate.get("redrob_signals", {})
        
        deduction = 0.0
        
        # Check contact verification flags
        if not signals.get("verified_email", False):
            deduction += 0.15
        if not signals.get("verified_phone", False):
            deduction += 0.15
            
        # Check for placeholder names or emails
        name = str(profile.get("anonymized_name", "")).lower()
        if any(placeholder in name for placeholder in ("test", "example", "dummy", "john doe", "jane doe")):
            deduction += 0.50
            
        # Check email format placeholders in case raw email is present (if any)
        email = str(profile.get("email", "")).lower()
        if email and any(domain in email for domain in ("example.com", "test.com", "dummy.com", "placeholder.com")):
            deduction += 0.50
            
        return deduction
