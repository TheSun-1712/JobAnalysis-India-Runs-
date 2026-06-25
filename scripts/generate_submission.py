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
from redrob_ranker.xlsx_writer import write_xlsx  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate top-100 candidate ranking CSV and XLSX")
    parser.add_argument("--bundle", required=True, help="Path to the Redrob bundle directory")
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument("--output-xlsx", help="Output XLSX path (defaults to CSV path with .xlsx suffix)")
    parser.add_argument("--top-n", type=int, default=100, help="Number of ranked candidates to emit")
    args = parser.parse_args()

    rows = rank_top_candidates(args.bundle, top_n=args.top_n)

    # 1. Write CSV
    output_csv = Path(args.output)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
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
    print(f"Wrote {len(rows)} ranked rows to CSV: {output_csv}")

    # 2. Write XLSX
    xlsx_path_str = args.output_xlsx
    if not xlsx_path_str:
        if output_csv.suffix.lower() == ".csv":
            xlsx_path = output_csv.with_suffix(".xlsx")
        else:
            xlsx_path = output_csv.parent / (output_csv.name + ".xlsx")
    else:
        xlsx_path = Path(xlsx_path_str)

    write_xlsx(rows, xlsx_path)
    print(f"Wrote {len(rows)} ranked rows to XLSX: {xlsx_path}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
