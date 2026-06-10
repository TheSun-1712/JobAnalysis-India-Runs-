from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from redrob_ranker.pdf_deck import build_deck_pages, write_pdf  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PDF deck")
    parser.add_argument("--output", required=True, help="PDF output path")
    parser.add_argument("--submission", default="submission.csv", help="Submission CSV filename to mention")
    parser.add_argument("--deck-name", default="deck.pdf", help="Deck filename to mention")
    args = parser.parse_args()

    pages = build_deck_pages({"submission": args.submission, "deck": args.deck_name})
    path = write_pdf(pages, args.output)
    print(f"Wrote deck to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
