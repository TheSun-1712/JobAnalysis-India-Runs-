from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any
from ..bundle import iter_candidate_records, extract_docx_text
from ..job_description import parse_job_description, ROLE_TERMS

from .heuristic import HeuristicAgent
from .tfidf import TfidfAgent, tokenize
from .bm25 import Bm25Agent
from .semantic import SemanticAgent
from .llm import LlmAgent
from .jaccard import JaccardAgent
from .constraints import ConstraintsAgent
from .seniority import SeniorityAgent
from .prestige import PrestigeAgent
from .stability import StabilityAgent
from .research import ResearchAgent
from .association import AssociationAgent
from .github import GithubAgent
from .certifications import CertificationsAgent
from .language import LanguageAgent
from .project import ProjectAgent
from .assessment import AssessmentAgent
from .engagement import EngagementAgent
from .compensation import CompensationAgent
from .tone import ToneAgent

class MasterAgent:
    def __init__(self, bundle_dir: str | Path) -> None:
        self.bundle = Path(bundle_dir)
        self.jd_text = extract_docx_text(self.bundle / "job_description.docx")
        self.jd = parse_job_description(self.jd_text)
        self.corpus_stats: dict[str, Any] = {}

    def compute_corpus_stats(self) -> None:
        """Run a fast initial pass over the candidates dataset to calculate global document stats, using cache if available."""
        cache_path = self.bundle / "corpus_stats.json"
        if cache_path.exists():
            try:
                with cache_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if "base_salary" in data and "salary_per_year" in data:
                    self.corpus_stats = {
                        "vocab": set(data["vocab"]),
                        "N": data["N"],
                        "df": data["df"],
                        "avgdl": data["avgdl"],
                        "jd_text": self.jd_text,
                        "base_salary": data["base_salary"],
                        "salary_per_year": data["salary_per_year"]
                    }
                    return
            except Exception:
                pass

        source = self.bundle / "candidates.jsonl"
        if not source.exists():
            gz = self.bundle / "candidates.jsonl.gz"
            if gz.exists():
                source = gz
            else:
                raise FileNotFoundError("candidates.jsonl or candidates.jsonl.gz not found in bundle")

        # Vocabulary: union of job description tokens and core technology keys
        jd_tokens = tokenize(self.jd_text)
        vocab = set(jd_tokens).union(ROLE_TERMS.keys())
        vocab = {v for v in vocab if len(v) >= 2 or v in {"r", "c", "c++", "c#", "go", "sql"}}

        N = 0
        total_len = 0
        df = {term: 0 for term in vocab}
        salaries = []

        from ..bundle import flatten_candidate_text
        for record in iter_candidate_records(source):
            N += 1
            text = flatten_candidate_text(record)
            tokens = tokenize(text)
            total_len += len(tokens)
            
            unique_tokens = set(tokens)
            for term in vocab:
                if term in unique_tokens:
                    df[term] += 1

            signals = record.get("redrob_signals", {})
            if isinstance(signals, dict):
                salary_range = signals.get("expected_salary_range_inr_lpa")
                if salary_range and isinstance(salary_range, dict):
                    min_expect = salary_range.get("min")
                    if min_expect is not None:
                        try:
                            min_expect = float(min_expect)
                            profile = record.get("profile", {})
                            years = float(profile.get("years_of_experience", 0.0))
                            if min_expect > 0.0:
                                salaries.append((min_expect, years))
                        except (ValueError, TypeError):
                            pass

        # Compute dynamic salary coefficients
        base_salary, salary_per_year = 12.0, 6.0
        if len(salaries) >= 5:
            sorted_sals = sorted(item[0] for item in salaries)
            n_sal = len(sorted_sals)
            if n_sal % 2 == 1:
                median_sal = sorted_sals[n_sal // 2]
            else:
                median_sal = (sorted_sals[n_sal // 2 - 1] + sorted_sals[n_sal // 2]) / 2.0
            
            if 5.0 <= median_sal <= 100.0:
                base_salary = round(median_sal, 2)
                salary_per_year = round(median_sal * 0.5, 2)

        self.corpus_stats = {
            "vocab": vocab,
            "N": N,
            "df": df,
            "avgdl": total_len / N if N > 0 else 100.0,
            "jd_text": self.jd_text,
            "base_salary": base_salary,
            "salary_per_year": salary_per_year
        }

        # Cache the results
        try:
            cache_data = {
                "vocab": list(vocab),
                "N": N,
                "df": df,
                "avgdl": self.corpus_stats["avgdl"],
                "base_salary": base_salary,
                "salary_per_year": salary_per_year
            }
            with cache_path.open("w", encoding="utf-8") as f:
                json.dump(cache_data, f)
        except Exception:
            pass

    def get_dynamic_weights(self) -> dict[str, float]:
        """Compute candidate ranking ensemble weights dynamically based on job description characteristics."""
        weights = {
            "Heuristics": 1.5,
            "Simulated LLM": 1.5,
            "BM25": 1.5,
            "TF-IDF": 1.0,
            "Semantic": 1.0,
            "Jaccard Overlap": 1.0,
            "Seniority": 1.0,
            "Company Prestige": 1.0,
            "Github Activity": 1.0,
            "Constraints": 0.6,
            "Job Stability": 0.6,
            "Research & Publications": 0.6,
            "Skill Associations": 0.6,
            "Certifications": 0.6,
            "Languages": 0.6,
            "Side Projects": 0.6,
            "Verified Assessments": 0.6,
            "Talent Engagement": 0.6,
            "Salary Alignment": 0.6,
            "Profile Readability": 0.6,
        }

        # Check job description and requirements for dynamic adjustments
        jd_text_lower = self.jd_text.lower()

        # 1. Experience Requirements adjusting Seniority vs. Side Projects/Certifications
        min_exp = self.jd.experience_min
        if min_exp >= 6.0:
            weights["Seniority"] = round(weights["Seniority"] * 1.5, 2)
            weights["Side Projects"] = round(weights["Side Projects"] * 0.6, 2)
            weights["Certifications"] = round(weights["Certifications"] * 0.6, 2)
        elif min_exp <= 2.0:
            weights["Seniority"] = round(weights["Seniority"] * 0.5, 2)
            weights["Side Projects"] = round(weights["Side Projects"] * 1.8, 2)
            weights["Certifications"] = round(weights["Certifications"] * 1.8, 2)

        # 2. Research focus
        research_keywords = {"research", "publication", "publications", "paper", "papers", "patent", "patents", "phd", "ph.d"}
        if any(kw in jd_text_lower for kw in research_keywords):
            weights["Research & Publications"] = round(weights["Research & Publications"] * 2.0, 2)

        # 3. Github/Open Source focus
        github_keywords = {"github", "git ", "open source", "open-source", "contribution", "contributions", "portfolio"}
        if any(kw in jd_text_lower for kw in github_keywords):
            weights["Github Activity"] = round(weights["Github Activity"] * 1.5, 2)

        # 4. Salary & Budget focus
        salary_keywords = {"salary", "budget", "compensation", "lpa", "inr"}
        if any(kw in jd_text_lower for kw in salary_keywords):
            weights["Salary Alignment"] = round(weights["Salary Alignment"] * 1.5, 2)

        # 5. Strict Location / Relocation constraint sensitivity
        if self.jd.location_terms or "onsite" in jd_text_lower or "hybrid" in jd_text_lower:
            weights["Constraints"] = round(weights["Constraints"] * 1.8, 2)

        return weights

    def run_ensemble_ranking(self, top_n: int = 100) -> list[dict[str, Any]]:
        """Stream candidates, evaluate them across all 20 sub-agents, and merge with WRRF."""
        if not self.corpus_stats:
            self.compute_corpus_stats()

        # Initialize sub-agents
        agents = {
            "Heuristics": HeuristicAgent(self.jd, self.corpus_stats),
            "TF-IDF": TfidfAgent(self.jd, self.corpus_stats),
            "BM25": Bm25Agent(self.jd, self.corpus_stats),
            "Semantic": SemanticAgent(self.jd, self.corpus_stats),
            "Simulated LLM": LlmAgent(self.jd, self.corpus_stats),
            "Jaccard Overlap": JaccardAgent(self.jd, self.corpus_stats),
            "Constraints": ConstraintsAgent(self.jd, self.corpus_stats),
            "Seniority": SeniorityAgent(self.jd, self.corpus_stats),
            "Company Prestige": PrestigeAgent(self.jd, self.corpus_stats),
            "Job Stability": StabilityAgent(self.jd, self.corpus_stats),
            "Research & Publications": ResearchAgent(self.jd, self.corpus_stats),
            "Skill Associations": AssociationAgent(self.jd, self.corpus_stats),
            "Github Activity": GithubAgent(self.jd, self.corpus_stats),
            "Certifications": CertificationsAgent(self.jd, self.corpus_stats),
            "Languages": LanguageAgent(self.jd, self.corpus_stats),
            "Side Projects": ProjectAgent(self.jd, self.corpus_stats),
            "Verified Assessments": AssessmentAgent(self.jd, self.corpus_stats),
            "Talent Engagement": EngagementAgent(self.jd, self.corpus_stats),
            "Salary Alignment": CompensationAgent(self.jd, self.corpus_stats),
            "Profile Readability": ToneAgent(self.jd, self.corpus_stats),
        }

        source = self.bundle / "candidates.jsonl"
        if not source.exists():
            gz = self.bundle / "candidates.jsonl.gz"
            if gz.exists():
                source = gz

        # Early gatekeeper limits
        min_exp = self.jd.experience_min
        from ..job_description import INDIA_TIER1_MARKERS

        # Streaming pass evaluating candidates across all agents
        for record in iter_candidate_records(source):
            profile = record.get("profile", {})
            years = float(profile.get("years_of_experience", 0.0))
            
            # Gatekeeper 1: Experience checks (filter if years < min_exp - 3.0)
            if years < max(1.0, min_exp - 3.0):
                continue
                
            # Gatekeeper 2: Logistical/location checks (filter if outside India and unwilling to relocate)
            location = f"{profile.get('location', '')} {profile.get('country', '')}".lower()
            is_india = "india" in location
            has_pref = any(marker in location for marker in INDIA_TIER1_MARKERS)
            relocate = record.get("redrob_signals", {}).get("willing_to_relocate", False)
            
            if not is_india and not has_pref and not relocate:
                continue

            for agent in agents.values():
                agent.update(record, max_size=500)

        # Collect rankings
        agent_rankings = {}
        for name, agent in agents.items():
            agent_rankings[name] = agent.get_top_rankings()

        # Weighted Reciprocal Rank Fusion (WRRF)
        agent_weights = self.get_dynamic_weights()

        candidate_map = {}
        rrf_scores = {}
        candidate_ranks = {}
        k = 60

        for name, rankings in agent_rankings.items():
            weight = agent_weights.get(name, 1.0)
            for rank, (score, candidate) in enumerate(rankings, start=1):
                cid = candidate["candidate_id"]
                candidate_map[cid] = candidate
                if cid not in rrf_scores:
                    rrf_scores[cid] = 0.0
                    candidate_ranks[cid] = {}
                
                # Apply agent weighting
                rrf_scores[cid] += weight / (k + rank)
                candidate_ranks[cid][name] = rank

        # Deterministic sorting key: 1. RRF score descending, 2. Years experience descending, 3. Candidate ID ascending
        def sorting_key(cid: str) -> tuple[float, float, int]:
            rrf_val = -rrf_scores[cid]
            years = -float(candidate_map[cid].get("profile", {}).get("years_of_experience", 0.0))
            try:
                cid_num = int(str(cid).split("_")[-1])
            except Exception:
                cid_num = 10**9
            return rrf_val, years, cid_num

        sorted_cids = sorted(rrf_scores.keys(), key=sorting_key)
        top_cids = sorted_cids[:top_n]
        
        rows = []
        previous_score = None
        for rank, cid in enumerate(top_cids, start=1):
            candidate = candidate_map[cid]
            
            score = 0.99 - (rank * 0.002)
            if previous_score is not None and score >= previous_score:
                score = previous_score - 0.001
            previous_score = score
            
            ranks_info = candidate_ranks[cid]
            profile = candidate.get("profile", {})
            title = profile.get("current_title", "Engineer")
            years = profile.get("years_of_experience", 0.0)
            
            cand_skills = {str(s.get("name", "")).lower() for s in candidate.get("skills", []) if s.get("name")}
            target_skills = {term.lower() for term in self.jd.required_terms.keys()}
            matched_skills = sorted(list(cand_skills.intersection(target_skills)))
            skills_str = ", ".join(matched_skills[:4]) if matched_skills else "matching core stack"

            agent_highlights = {
                "Heuristics": "excellent profile completeness and structured details",
                "TF-IDF": "strong matching keywords in resume text",
                "BM25": "highly relevant match with job description keywords",
                "Semantic": "strong alignment with the core tech stack and domain",
                "Simulated LLM": "high rating on qualifications and skills screening",
                "Jaccard Overlap": "broad coverage of matching skills and related areas",
                "Constraints": "full alignment with location and work mode constraints",
                "Seniority": "consistent career progression and seniority",
                "Company Prestige": "prior experience at top-tier companies",
                "Job Stability": "strong tenure stability with low job-hopping risk",
                "Research & Publications": "strong academic and research credentials",
                "Skill Associations": "proven familiarity with related tech stacks and adjacent areas",
                "Github Activity": "active open-source contributions and coding footprints",
                "Certifications": "highly relevant professional certifications",
                "Languages": "strong communication and language skills",
                "Side Projects": "solid portfolio of side projects and coding tasks",
                "Verified Assessments": "excellent scores on technical skill assessments",
                "Talent Engagement": "high recruiter response rate and activity",
                "Salary Alignment": "expected salary aligned with the target budget bracket",
                "Profile Readability": "clear and professionally formatted resume layout"
            }

            sorted_agent_ranks = sorted(ranks_info.items(), key=lambda x: x[1])
            standout_agents = [name for name, r in sorted_agent_ranks if r <= 60][:3]
            strengths = [agent_highlights[name] for name in standout_agents]

            if strengths:
                if len(strengths) == 3:
                    strength_desc = f"(1) {strengths[0]}, (2) {strengths[1]}, and (3) {strengths[2]}"
                elif len(strengths) == 2:
                    strength_desc = f"(1) {strengths[0]} and (2) {strengths[1]}"
                else:
                    strength_desc = f"(1) {strengths[0]}"
                review_body = f"Top standout factors: {strength_desc}."
            else:
                review_body = "Selected based on balanced overall metrics across multiple agents."
                
            skills_body = f"Core technical alignment includes: {skills_str}."
            reasoning = f"Recommended for {title} ({years} years of experience). {review_body} {skills_body}"

            rows.append({
                "candidate_id": cid,
                "rank": rank,
                "score": round(score, 6),
                "reasoning": reasoning,
            })
            
        return rows
