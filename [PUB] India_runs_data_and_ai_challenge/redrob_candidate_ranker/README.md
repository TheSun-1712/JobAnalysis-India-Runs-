# Redrob Candidate Ranker

Hybrid CPU-only candidate ranking pipeline for the Redrob hackathon bundle.

## What it does

- Reads the released job description from the bundle.
- Streams `candidates.jsonl` without loading the full 100k records into memory.
- Scores candidates with a hybrid model that combines semantic term matching, structured fit, availability, and trust/plausibility signals.
- Produces a top-100 CSV in the exact validator format.
- Generates a short PDF deck explaining the approach.

## Layout

- `src/redrob_ranker/` core ranking code
- `scripts/generate_submission.py` creates the ranked CSV
- `scripts/build_deck.py` creates the PDF deck

## Run

```bash
python scripts/generate_submission.py --bundle "e:/Projects/India Runs/[PUB] India_runs_data_and_ai_challenge/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge" --output submission.csv
python scripts/build_deck.py --bundle "e:/Projects/India Runs/[PUB] India_runs_data_and_ai_challenge/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge" --output deck.pdf
python "e:/Projects/India Runs/[PUB] India_runs_data_and_ai_challenge/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py" submission.csv
```

The code uses only the Python standard library and is designed to stay well inside the 5-minute CPU budget on the released dataset.
