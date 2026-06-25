from __future__ import annotations

from pathlib import Path
from typing import Any

from .agents import MasterAgent


def rank_top_candidates(bundle_dir: str | Path, top_n: int = 100) -> list[dict[str, Any]]:
    master = MasterAgent(bundle_dir)
    return master.run_ensemble_ranking(top_n=top_n)
