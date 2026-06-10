from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker.ranker import rank_top_candidates  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate top-100 candidate ranking CSV")
    parser.add_argument("--bundle", required=True, help="Path to the Redrob bundle directory")
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument("--top-n", type=int, default=100, help="Number of ranked candidates to emit")
    args = parser.parse_args()

    rows = rank_top_candidates(args.bundle, top_n=args.top_n)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "candidate_id": row["candidate_id"],
                    "rank": row["rank"],
                    "score": f"{row['score']:.6f}",
                    "reasoning": row["reasoning"],
                }
            )

    print(f"Wrote {len(rows)} ranked rows to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
