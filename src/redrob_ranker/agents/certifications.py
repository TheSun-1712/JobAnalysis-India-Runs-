from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..job_description import JobDescriptionProfile

RELEVANT_CERT_KEYWORDS = {
    "aws", "amazon web services", "azure", "gcp", "google cloud", "kubernetes", 
    "cka", "ckad", "scrum", "scrummaster", "pmp", "tensorflow", "cloudera", 
    "snowflake", "databricks", "nvidia", "deep learning", "machine learning"
}

class CertificationsAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        certs = candidate.get("certifications", [])
        if not certs:
            return 0.0
            
        score = 0.0
        for cert in certs:
            name = str(cert.get("name", "")).lower()
            # If the certification name matches any of our target keywords, award points
            if any(kw in name for kw in RELEVANT_CERT_KEYWORDS):
                score += 1.5
            else:
                score += 0.3 # General minor point for other certifications
                
        return min(5.0, score)
