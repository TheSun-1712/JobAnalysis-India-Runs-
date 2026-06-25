# Redrob Candidate Ranker

A highly optimized, 20-Agent Ensemble candidate discovery and ranking system developed for the Redrob hackathon. It utilizes a Weighted Reciprocal Rank Fusion (WRRF) architecture to aggregate ranking predictions across multiple dimensions, running purely on CPU-only standard Python libraries in a streaming fashion.

---

## 20-Agent Ensemble Architecture

The system evaluates candidates along 20 distinct, specialized axes. Each axis is managed by a dedicated agent inheriting from `BaseAgent`:

### 1. Relevance & Matching Agents
* **HeuristicAgent**: Rules-based profile scoring mapping profile completeness, background alignment, and candidate availability.
* **TfidfAgent**: Cosine similarity of TF-IDF vectors calculated on streaming candidate tokens.
* **Bm25Agent**: Probabilistic Okapi BM25 ranking model, normalized against the global average document length.
* **SemanticAgent**: Expands core job description concepts using synonyms to perform soft-concept keyword matching.
* **JaccardAgent**: Evaluates set-overlap similarity of skills to measure stack coverage without keyword-frequency bias.
* **LlmAgent**: Simulates zero-shot LLM screening using a multi-criteria scoring rubric (technical stack, title, quality of achievements, and credentials).

### 2. Career Path & Stability Agents
* **SeniorityAgent**: Analyzes title progression timelines to evaluate career seniority.
* **PrestigeAgent**: Multiplier-based prestige scoring prioritizing candidates from elite global and regional technology brands.
* **StabilityAgent**: Evaluates median job tenure, penalizing frequent job-hopping profiles.
* **ResearchAgent**: Detects academic publications, patents, research-specific degrees (PhD/MS), and related research titles.

### 3. Competency & Activity Agents
* **GithubAgent**: Scans GitHub activity scores and Git keywords in profile summaries.
* **CertificationsAgent**: Evaluates professional cloud (AWS, GCP, Azure), systems engineering (Kubernetes, Scrum), and ML credentials.
* **LanguageAgent**: Ranks communication suitability focusing on English fluency and multilingual capabilities.
* **ProjectAgent**: Awards points for side projects, hackathons, and competitive coding contributions (e.g. Kaggle).
* **AssessmentAgent**: Scores performance on platform-verified technical assessments matching the target stack.

### 4. Logistics, Alignment & Platform Signals
* **ConstraintsAgent**: Computes compliance checks against logistical limits (location preference, work mode, and experience bounds).
* **EngagementAgent**: Aggregates platform signals including profile views, connection counts, recruiter saves, and interview completion rates.
* **CompensationAgent**: Rates expected compensation brackets relative to candidate experience.
* **ToneAgent**: Evaluates the professional formatting structure, readability, and vocabulary of resume summaries.

---

## Weighted Reciprocal Rank Fusion (WRRF)

The **Master Agent** aggregates rankings returned by all 20 sub-agents using Weighted Reciprocal Rank Fusion (WRRF) to compute the ensembled score:

$$\text{WRRF Score}(c) = \sum_{a \in \text{Agents}} \frac{w_a}{k + \text{Rank}_a(c)}$$

Where:
* $k = 60$ (constant).
* $w_a$ represents the agent weight:
  * **Primary (1.5x)**: Heuristics, Simulated LLM, BM25.
  * **Secondary (1.0x)**: TF-IDF, Semantic, Jaccard Overlap, Seniority, Company Prestige, Github Activity.
  * **Tertiary (0.6x)**: Constraints, Job Stability, Research & Publications, Skill Associations, Certifications, Languages, Side Projects, Verified Assessments, Talent Engagement, Salary Alignment, Profile Readability.

### Deterministic Tie-Breaking
To guarantee complete reproducibility and strict score monotonicity:
1. Sorted by **Weighted RRF score** (descending).
2. Sorted by **Years of experience** (descending).
3. Sorted by **Candidate ID numeric sequence** (ascending).

---

## Dual Output Formats (CSV & XLSX)

The pipeline outputs the top-100 recommended candidates in two formats simultaneously:
1. **CSV Format**: Matches the required validator format exactly.
2. **XLSX Excel Format**: Formatted using a lightweight, standard-library-only Excel OpenXML zip writer (`xlsx_writer.py`) which ensures compatibility with Excel, Sheets, and LibreOffice without adding external library dependencies.

The reasoning column in both files contains a concise, highly readable, structured list of the top 3 standout factors representing the candidate's core strengths (e.g. `Top standout factors: (1) high BM25 search relevance matching, (2) optimal TF-IDF keyword relevance score, and (3) strong semantic concept alignment.`).

---

## Caching & Speed Optimization

To stream 100k candidate records (`candidates.jsonl`, 487MB) efficiently under 15 seconds:
* The pipeline performs a fast, tokenized streaming first pass to compute global term frequencies and average document lengths.
* It caches these statistics to `data/corpus_stats.json` so that subsequent runs execute almost instantaneously.
* Apply early logistical gatekeeper pre-filtering during streaming to skip scoring for candidates who do not meet basic experience or relocation bounds.

---

## Run Commands

Generate candidate rankings:
```bash
python scripts/generate_submission.py --bundle data --output submission.csv
```

Validate the submission CSV formatting:
```bash
python validate_submission.py submission.csv
```

Generate the presentation PDF deck:
```bash
python scripts/build_deck.py --output deck.pdf
```
