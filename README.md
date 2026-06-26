# Redrob Candidate Ranker & ATS Pipeline

This repository contains two production-grade candidate evaluation systems for the **Redrob Hackathon**:

1. **Dynamic ATS Pipeline (`ats_pipeline.py`)**: An advanced, memory-optimized Applicant Tracking System pipeline equipped with dynamic job description parsing, rule/statistical fraud detection, synonym-expanded BM25 scoring, and an online **Reinforcement Learning (LinUCB Contextual Bandit)** feedback model.
2. **Redrob Candidate Ranker**: A standard-library-only hybrid streaming ranker designed for high-throughput candidate scoring under the 5-minute sandbox constraints.

---

## 🚀 1. Dynamic ATS Pipeline (`ats_pipeline.py`)

### Core Features
* **Memory Optimization**: Streams candidates sequentially from gzip archives (`candidates.jsonl.gz`), maintaining an $O(1)$ memory footprint or $O(N)$ bound by the heap.
* **JD Parsing (spaCy + regex)**: Dynamically extracts target experience bounds and core technical skills using spaCy Part-of-Speech tagging at runtime.
* **Fake/Honeypot Detection (Rules + IsolationForest)**: Filters fraud candidates by comparing experience durations against framework release dates, and flags structural outliers using an Isolation Forest.
* **Multi-Dimensional Scorer**: Computes a compound score using:
  * **Semantic BM25** with synonym query expansion (e.g. mapping `llm` to RAG, GPT, llama).
  * Exact skills match ratio.
  * Gaussian experience curve centered on target experience.
  * Project action-verb matching.
* **RL Contextual Bandit (LinUCB)**: Learns recruiter selection patterns dynamically by adjusting scoring weights in real time based on shortlist interaction rewards.
* **MMR Diversity Pass**: Adjusts candidate ranking to minimize redundancy and promote profile diversity using Jaccard text similarity.

### Run the ATS Pipeline & Simulation
Execute the pipeline and its dynamic recruiter feedback learning simulation using the virtual environment interpreter:
```bash
python ats_pipeline.py
```
*Outputs generated:*
* `mock_submission.csv`: Shortlisted top candidates.
* `mock_audit.jsonl`: Audit trail log of flagged/fraudulent profiles.

---

## 🛠️ 2. Redrob Candidate Ranker

A fast, lightweight hybrid pipeline that streams and ranks the 100k candidate dataset against a job description.

### Run the Ranker
```bash
python scripts/generate_submission.py --bundle data --output submission.csv
python scripts/build_deck.py --output deck.pdf
python validate_submission.py submission.csv
```

---

## 📦 Installation & Setup

1. **Configure Virtual Environment**:
   Ensure Python 3.11+ is active in `.venv`.
2. **Install Package & Dependencies**:
   ```bash
   pip install -e .
   pip install spacy scikit-learn numpy rank-bm25 click
   python -m spacy download en_core_web_sm
   ```
