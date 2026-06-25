from __future__ import annotations
import re
from typing import Any
from .base import BaseAgent
from ..job_description import JobDescriptionProfile

class LlmAgent(BaseAgent):
    def score_candidate(self, candidate: dict[str, Any]) -> float:
        # Rubric 1: Technical Stack Alignment (0 to 5)
        tech_score = self._evaluate_tech_alignment(candidate)
        
        # Rubric 2: Role & Title Suitability (0 to 5)
        role_score = self._evaluate_role_suitability(candidate)
        
        # Rubric 3: Quality & Achievements (0 to 5)
        quality_score = self._evaluate_quality_achievements(candidate)
        
        # Rubric 4: Education & Credentials (0 to 5)
        education_score = self._evaluate_education(candidate)
        
        base_score = tech_score + role_score + quality_score + education_score
        deduction = self.get_profile_authenticity_deduction(candidate)
        return max(0.0, base_score - deduction)

    def _evaluate_tech_alignment(self, candidate: dict[str, Any]) -> float:
        skills = {str(s.get("name", "")).lower() for s in candidate.get("skills", []) if s.get("name")}
        if not skills:
            return 0.0
        
        target_skills = {term.lower() for term in self.jd.required_terms.keys()}
        if not target_skills:
            target_skills = {"python", "sql", "embeddings", "ranking", "retrieval", "vector search", "llm"}
            
        matched = skills.intersection(target_skills)
        ratio = len(matched) / len(target_skills) if target_skills else 0.0
        return min(5.0, ratio * 7.5)

    def _evaluate_role_suitability(self, candidate: dict[str, Any]) -> float:
        history = candidate.get("career_history", [])
        profile = candidate.get("profile", {})
        current_title = str(profile.get("current_title", "")).lower()
        
        titles = [current_title]
        for job in history:
            title = str(job.get("title", "")).lower()
            if title:
                titles.append(title)
                
        is_senior = any(any(senior in t for senior in ("senior", "sr", "lead", "principal", "architect", "head", "manager")) for t in titles)
        is_ai_ml = any(any(keyword in t for keyword in ("ai", "ml", "machine learning", "nlp", "recommendation", "search", "ranking", "deep learning")) for t in titles)
        is_engineer = any(any(eng in t for eng in ("engineer", "scientist", "developer", "programmer")) for t in titles)
        
        if is_ai_ml and is_senior and is_engineer:
            return 5.0
        elif is_ai_ml and is_engineer:
            return 4.0
        elif is_senior and is_engineer:
            return 3.0
        elif is_engineer:
            return 2.0
        return 0.5

    def _evaluate_quality_achievements(self, candidate: dict[str, Any]) -> float:
        history = candidate.get("career_history", [])
        if not history:
            return 0.0
            
        descriptions = [str(job.get("description", "")) for job in history if job.get("description")]
        if not descriptions:
            return 0.5
            
        full_text = " ".join(descriptions).lower()
        has_metrics = bool(re.search(r"\b\d+%\b|\b\d+\s*percent\b|\b\d+x\b|\b\d+m\b|\b\d+k\b", full_text))
        
        optimizations = sum(1 for kw in ("optimize", "optimized", "optimization", "reduce", "reduced", "improve", "improved", "improvement", "scale", "scaled", "scaling", "speed", "accelerate", "save", "saved") if kw in full_text)
        achievements = sum(1 for kw in ("design", "designed", "architect", "architected", "deploy", "deployed", "built", "implemented", "launched", "led", "directed") if kw in full_text)
        
        score = 1.0
        if has_metrics:
            score += 1.5
        if optimizations >= 2:
            score += 1.5
        elif optimizations == 1:
            score += 0.8
        if achievements >= 2:
            score += 1.0
        elif achievements == 1:
            score += 0.5
            
        return min(5.0, score)

    def _evaluate_education(self, candidate: dict[str, Any]) -> float:
        education = candidate.get("education", [])
        if not education:
            return 0.0
            
        scores = []
        for edu in education:
            degree = str(edu.get("degree", "")).lower()
            field = str(edu.get("field_of_study", "")).lower()
            inst = str(edu.get("institution", "")).lower()
            tier = str(edu.get("tier", "")).lower()
            
            edu_score = 1.5
            is_cs_it = any(kw in field for kw in ("computer science", "cs", "it", "information technology", "data science", "artificial intelligence", "ai", "machine learning", "ml", "math", "statistics", "software"))
            if is_cs_it:
                edu_score += 1.0
                
            if any(kw in degree for kw in ("phd", "ph.d", "doctorate", "doctor")):
                edu_score += 1.5
            elif any(kw in degree for kw in ("master", "m.tech", "ms", "m.s", "m.e", "msc")):
                edu_score += 1.0
            elif any(kw in degree for kw in ("bachelor", "b.tech", "be", "b.e", "bs", "b.s")):
                edu_score += 0.5
                
            if "tier-1" in tier or "tier 1" in tier or any(kw in inst for kw in ("iit", "indian institute of technology", "bits pilani", "iisc", "iiit", "stanford", "mit", "berkeley", "cmu")):
                edu_score += 1.0
                
            scores.append(edu_score)
            
        return min(5.0, max(scores)) if scores else 0.0
