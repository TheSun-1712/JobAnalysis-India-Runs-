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

class Bm25Agent(BaseAgent):
    def __init__(self, jd: JobDescriptionProfile, corpus_stats: dict[str, Any] | None = None) -> None:
        super().__init__(jd, corpus_stats)
        self.vocab = self.corpus_stats.get("vocab", set())
        self.N = self.corpus_stats.get("N", 1)
        self.df = self.corpus_stats.get("df", {})
        self.avgdl = self.corpus_stats.get("avgdl", 100.0)

        # Precompute positive-only BM25 IDF variant for vocabulary terms
        self.idf: dict[str, float] = {}
        for term in self.vocab:
            df_val = self.df.get(term, 0)
            self.idf[term] = math.log(1.0 + (self.N - df_val + 0.5) / (df_val + 0.5))

        self.k1 = 1.5
        self.b = 0.75

    def score_candidate(self, candidate: dict[str, Any]) -> float:
        candidate_text = flatten_candidate_text(candidate)
        tokens = tokenize(candidate_text)
        if not tokens:
            return 0.0
        
        counts = Counter(tokens)
        doc_len = len(tokens)
        
        score = 0.0
        for term in self.vocab:
            freq = counts.get(term, 0)
            if freq == 0:
                continue
            
            idf_val = self.idf.get(term, 0.0)
            numerator = freq * (self.k1 + 1.0)
            denominator = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
            
            score += idf_val * (numerator / denominator)
            
        return score
