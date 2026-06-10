from __future__ import annotations

import heapq
from pathlib import Path
from typing import Any

from .bundle import extract_docx_text, iter_candidate_records
from .features import rank_key, scaled_score, score_candidate
from .job_description import parse_job_description
from .reasoning import build_reasoning


def _candidate_number(candidate_id: str) -> int:
    try:
        return int(candidate_id.split("_")[-1])
    except Exception:
        return 10**9


def rank_top_candidates(bundle_dir: str | Path, top_n: int = 100) -> list[dict[str, Any]]:
    bundle = Path(bundle_dir)
    jd_text = extract_docx_text(bundle / "job_description.docx")
    jd = parse_job_description(jd_text)
    source = bundle / "candidates.jsonl"
    if not source.exists():
        gz = bundle / "candidates.jsonl.gz"
        if gz.exists():
            source = gz
        else:
            raise FileNotFoundError("candidates.jsonl or candidates.jsonl.gz not found in bundle")

    heap: list[tuple[float, int, dict[str, Any], dict[str, Any]]] = []
    for candidate in iter_candidate_records(source):
        raw_score, signal = score_candidate(candidate, jd)
        heap_key = rank_key(candidate, raw_score)
        entry = (heap_key[0], heap_key[1], candidate, signal)
        if len(heap) < top_n:
            heapq.heappush(heap, entry)
        elif entry > heap[0]:
            heapq.heapreplace(heap, entry)

    selected = sorted(heap, key=lambda item: (-item[0], _candidate_number(str(item[2].get("candidate_id", "")))))

    rows: list[dict[str, Any]] = []
    previous_score = None
    for rank, (raw_score, _secondary, candidate, signal) in enumerate(selected, start=1):
        score = scaled_score(raw_score) - (rank * 1e-4)
        if previous_score is not None and score > previous_score:
            score = previous_score - 1e-4
        previous_score = score
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "rank": rank,
                "score": round(score, 6),
                "reasoning": build_reasoning(candidate, signal),
                "raw_score": raw_score,
            }
        )

    for index in range(1, len(rows)):
        if rows[index]["score"] > rows[index - 1]["score"]:
            rows[index]["score"] = rows[index - 1]["score"] - 0.0001

    return rows
