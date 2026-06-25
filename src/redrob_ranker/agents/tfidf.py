from __future__ import annotations
import math
import re
from collections import Counter
from typing import Any
from .base import BaseAgent
from ..bundle import flatten_candidate_text
from ..job_description import JobDescriptionProfile

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9\+\#\-/']+", text.lower())

class TfidfAgent(BaseAgent):
    def __init__(self, jd: JobDescriptionProfile, corpus_stats: dict[str, Any] | None = None) -> None:
        super().__init__(jd, corpus_stats)
        self.vocab = self.corpus_stats.get("vocab", set())
        self.N = self.corpus_stats.get("N", 1)
        self.df = self.corpus_stats.get("df", {})

        # Precompute query weights (IDF of vocabulary terms in JD)
        self.query_weights: dict[str, float] = {}
        for term in self.vocab:
            df_val = self.df.get(term, 0)
            idf = math.log(1.0 + (self.N / (1.0 + df_val)))
            self.query_weights[term] = idf
        
        # Calculate L2 norm of query vector
        sum_sq = sum(w * w for w in self.query_weights.values())
        self.query_norm = math.sqrt(sum_sq) if sum_sq > 0 else 1.0

    def score_candidate(self, candidate: dict[str, Any]) -> float:
        candidate_text = flatten_candidate_text(candidate)
        tokens = tokenize(candidate_text)
        if not tokens:
            return 0.0
        
        counts = Counter(tokens)
        total_tokens = len(tokens)
        
        dot_product = 0.0
        candidate_sum_sq = 0.0
        
        for term in self.vocab:
            tf = counts.get(term, 0) / total_tokens
            df_val = self.df.get(term, 0)
            idf = math.log(1.0 + (self.N / (1.0 + df_val)))
            cand_weight = tf * idf
            
            candidate_sum_sq += cand_weight * cand_weight
            dot_product += self.query_weights.get(term, 0.0) * cand_weight
            
        candidate_norm = math.sqrt(candidate_sum_sq)
        if self.query_norm == 0.0 or candidate_norm == 0.0:
            return 0.0
        
        return dot_product / (self.query_norm * candidate_norm)
