from __future__ import annotations

import unittest
from typing import Any

from redrob_ranker import config
from redrob_ranker.features import (
    EVALUATORS,
    score_candidate,
)
from redrob_ranker.job_description import JobDescriptionProfile


class TestCandidateRanker(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_jd = JobDescriptionProfile(
            title="Senior AI Engineer",
            location_text="Pune, India",
            country_text="india",
            work_mode="hybrid",
            experience_min=5.0,
            experience_max=9.0,
            target_experience=7.0,
            required_terms={"embeddings": 3.0, "retrieval": 3.0},
            desired_terms={"evaluation": 1.4},
            disqualifier_terms=("pure research",),
            location_terms=("pune",),
        )

        self.mock_candidate = {
            "candidate_id": "CAND_0000001",
            "profile": {
                "anonymized_name": "John Doe",
                "headline": "Experienced AI Engineer specializing in embeddings and retrieval",
                "summary": "Building production ranking systems and vector search models.",
                "location": "Pune, Maharashtra",
                "country": "India",
                "years_of_experience": 7.0,
                "current_title": "AI Engineer",
                "current_company": "Acme Corp",
                "current_company_size": "51-200",
                "current_industry": "Software",
            },
            "career_history": [
                {
                    "company": "Acme Corp",
                    "title": "AI Engineer",
                    "start_date": "2021-01-01",
                    "end_date": None,
                    "duration_months": 36,
                    "is_current": True,
                    "industry": "Software",
                    "company_size": "51-200",
                    "description": "Designed embedding search, retrieval systems, and ranking engines.",
                },
                {
                    "company": "Infosys",
                    "title": "Software Developer",
                    "start_date": "2018-01-01",
                    "end_date": "2020-12-31",
                    "duration_months": 36,
                    "is_current": False,
                    "industry": "IT Services",
                    "company_size": "10001+",
                    "description": "Full stack software engineer using Python and SQL.",
                }
            ],
            "education": [
                {
                    "institution": "Pune University",
                    "degree": "B.Tech",
                    "field_of_study": "Computer Science",
                    "start_year": 2014,
                    "end_year": 2018,
                    "grade": "First Class",
                    "tier": "tier_2",
                }
            ],
            "skills": [
                {"name": "Python", "proficiency": "expert", "endorsements": 50, "duration_months": 60},
                {"name": "embeddings", "proficiency": "advanced", "endorsements": 20, "duration_months": 36},
                {"name": "retrieval", "proficiency": "intermediate", "endorsements": 10, "duration_months": 24},
            ],
            "certifications": [],
            "languages": [],
            "redrob_signals": {
                "profile_completeness_score": 90.0,
                "signup_date": "2023-01-01",
                "last_active_date": "2026-06-25",
                "open_to_work_flag": True,
                "profile_views_received_30d": 12,
                "applications_submitted_30d": 3,
                "recruiter_response_rate": 0.8,
                "avg_response_time_hours": 12.0,
                "skill_assessment_scores": {"Python": 95.0},
                "connection_count": 150,
                "endorsements_received": 80,
                "notice_period_days": 30,
                "expected_salary_range_inr_lpa": {"min": 25.0, "max": 35.0},
                "preferred_work_mode": "hybrid",
                "willing_to_relocate": True,
                "github_activity_score": 75.0,
                "search_appearance_30d": 45,
                "saved_by_recruiters_30d": 8,
                "interview_completion_rate": 0.95,
                "offer_acceptance_rate": 0.8,
                "verified_email": True,
                "verified_phone": True,
                "linkedin_connected": True,
            },
        }

    def test_config_loading(self) -> None:
        self.assertIn("semantic", config.WEIGHTS)
        self.assertEqual(config.WEIGHTS["semantic"], 1.85)
        self.assertEqual(config.SIGMOID_CENTER, 2.4)
        self.assertTrue(len(config.RELEVANT_SKILLS) > 0)
        self.assertIn("python", config.RELEVANT_SKILLS)

    def test_semantic_evaluator(self) -> None:
        text = "This candidate has experience in embeddings and retrieval."
        score = EVALUATORS["semantic"].evaluate(self.mock_candidate, self.mock_jd, text)
        # Should match both required terms (embeddings and retrieval) and some weights
        self.assertTrue(score > 0)
        self.assertLessEqual(score, 3.5)

    def test_title_evaluator(self) -> None:
        score, pattern = EVALUATORS["title"].evaluate(self.mock_candidate, self.mock_jd, "")
        self.assertEqual(pattern, "ai engineer")
        self.assertEqual(score, 1.0)

    def test_skills_evaluator(self) -> None:
        score, matched = EVALUATORS["skills"].evaluate(self.mock_candidate, self.mock_jd, "python embeddings retrieval")
        self.assertIn("Python", matched)
        self.assertIn("embeddings", matched)
        self.assertTrue(score > 0)

    def test_experience_evaluator(self) -> None:
        score = EVALUATORS["experience"].evaluate(self.mock_candidate, self.mock_jd, "")
        # Center is 7.0 and candidate has 7.0 experience, so should be close to 1.0 (gaussian peak)
        self.assertAlmostEqual(score, 1.0, places=2)

    def test_background_evaluator(self) -> None:
        score = EVALUATORS["background"].evaluate(self.mock_candidate, self.mock_jd, "")
        # Candidate worked at Acme Corp (product) and Infosys (consulting)
        self.assertTrue(-0.4 <= score <= 0.45)

    def test_location_evaluator(self) -> None:
        score = EVALUATORS["location"].evaluate(self.mock_candidate, self.mock_jd, "")
        # Pune is tier 1, and work mode hybrid matches Preferred work mode hybrid
        self.assertTrue(score > 0)

    def test_availability_evaluator(self) -> None:
        score = EVALUATORS["availability"].evaluate(self.mock_candidate, self.mock_jd, "")
        # Open to work, low notice period, verified contact details
        self.assertTrue(score > 0)

    def test_plausibility_evaluator(self) -> None:
        score = EVALUATORS["plausibility"].evaluate(self.mock_candidate, self.mock_jd, "")
        # Total experience is 7, career history dur_months is 36 + 36 = 72 months (6 years). Delta is 1.0 year.
        self.assertTrue(score > 0)

    def test_penalty_evaluator(self) -> None:
        score = EVALUATORS["penalty"].evaluate(self.mock_candidate, self.mock_jd, "embeddings retrieval")
        # No bad keywords, no penalty
        self.assertEqual(score, 0.0)

    def test_score_candidate_integration(self) -> None:
        raw_score, signal = score_candidate(self.mock_candidate, self.mock_jd)
        self.assertTrue(raw_score > 0)
        self.assertEqual(signal["title_pattern"], "ai engineer")
        self.assertEqual(signal["years"], 7.0)


if __name__ == "__main__":
    unittest.main()
