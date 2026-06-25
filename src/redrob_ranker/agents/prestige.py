from __future__ import annotations
from typing import Any
from .base import BaseAgent
from ..job_description import JobDescriptionProfile

TIER_1_COMPANIES = {
    "google", "microsoft", "amazon", "meta", "netflix", "uber", "apple", "linkedin", "airbnb", "salesforce", "adobe", "servicenow", "stripe", "openai", "nvidia"
}

TIER_2_COMPANIES = {
    "swiggy", "zomato", "flipkart", "paytm", "razorpay", "phonepe", "inmobi", "freshworks", "upgrad", "haptik", "ola", "meesho", "myntra", "jio", "zoho", "cred", "curefit", "byju's"
}

TIER_3_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", "hcl", "tech mahindra", "mindtree", "lti", "dxc"
}

class PrestigeAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        history = candidate.get("career_history", [])
        if not history:
            return 0.0
            
        score = 0.0
        for job in history:
            company = str(job.get("company", "")).strip().lower()
            duration_months = self.get_job_duration(job)
            duration_years = duration_months / 12.0
                
            # Determine prestige multiplier
            if any(c in company for c in TIER_1_COMPANIES):
                mult = 2.0
            elif any(c in company for c in TIER_2_COMPANIES):
                mult = 1.2
            elif any(c in company for c in TIER_3_COMPANIES):
                mult = 0.2
            else:
                mult = 0.6
                
            score += duration_years * mult
            
        return score
