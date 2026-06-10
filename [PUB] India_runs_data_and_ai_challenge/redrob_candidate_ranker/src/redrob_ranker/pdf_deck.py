from __future__ import annotations

from pathlib import Path


def _escape_pdf_text(text: str) -> str:
    safe = text.encode("latin-1", errors="replace").decode("latin-1")
    return safe.replace("\\", "\\\\").replace("(", r"\(").replace(")", r"\)")


def _wrap_lines(text: str, width: int = 88) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        extra = len(word) + (1 if current else 0)
        if current_len + extra > width and current:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += extra
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def _page_stream(title: str, bullets: list[str]) -> str:
    y = 760
    parts = ["BT", "/F1 18 Tf", f"72 {y} Td", f"({_escape_pdf_text(title)}) Tj"]
    y -= 30
    parts.append("/F1 11 Tf")
    for bullet in bullets:
        for line_index, line in enumerate(_wrap_lines(bullet, 88)):
            if y < 72:
                break
            text = ("- " if line_index == 0 else "  ") + line
            parts.append(f"72 {y} Td ({_escape_pdf_text(text)}) Tj")
            y -= 18
    parts.append("ET")
    return "\n".join(parts)


def write_pdf(pages: list[tuple[str, list[str]]], output_path: str | Path) -> Path:
    path = Path(output_path)
    content_objects = [_page_stream(title, bullets) for title, bullets in pages]

    objects: list[str] = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [" + " ".join(f"{4 + i * 2} 0 R" for i in range(len(pages))) + f"] /Count {len(pages)} >> endobj",
        "3 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
    ]

    for i, content in enumerate(content_objects):
        page_obj = 4 + i * 2
        stream_obj = page_obj + 1
        page = (
            f"{page_obj} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {stream_obj} 0 R >> endobj"
        )
        stream_obj_text = f"{stream_obj} 0 obj << /Length {len(content.encode('latin-1', errors='ignore'))} >> stream\n{content}\nendstream endobj"
        objects.extend([page, stream_obj_text])

    xref_positions = []
    header = "%PDF-1.4\n"
    body = []
    offset = len(header.encode("latin-1"))
    for obj in objects:
        xref_positions.append(offset)
        encoded = (obj + "\n").encode("latin-1")
        body.append(encoded)
        offset += len(encoded)

    xref_start = offset
    xref_lines = ["xref", f"0 {len(objects) + 1}", "0000000000 65535 f "]
    for pos in xref_positions:
        xref_lines.append(f"{pos:010d} 00000 n ")
    trailer = ["trailer", f"<< /Size {len(objects) + 1} /Root 1 0 R >>", "startxref", str(xref_start), "%%EOF"]

    with path.open("wb") as handle:
        handle.write(header.encode("latin-1"))
        for chunk in body:
            handle.write(chunk)
        handle.write(("\n".join(xref_lines + trailer) + "\n").encode("latin-1"))
    return path


def build_deck_pages(summary: dict[str, str]) -> list[tuple[str, list[str]]]:
    return [
        (
            "Redrob Candidate Ranker",
            [
                "Hybrid CPU-only ranking pipeline for 100k candidates under the hackathon constraints.",
                "Uses semantic term matching, structured fit, availability, and plausibility scoring.",
                f"Submission output: {summary.get('submission', 'top-100 CSV')}.",
            ],
        ),
        (
            "Data And Constraints",
            [
                "Candidate records contain profile, career history, education, skills, certifications, languages, and 23 behavioral signals.",
                "Validator requires exactly 100 ranked rows, unique candidate IDs, UTF-8 CSV, and monotonic scores.",
                "Ranking step must stay CPU-only, offline, under 5 minutes, and within 16 GB RAM.",
            ],
        ),
        (
            "Matching Strategy",
            [
                "Parse the JD into role terms, experience band, location preferences, and disqualifier hints.",
                "Score semantic overlap on embeddings, retrieval, ranking, LLM, evaluation, and production language.",
                "Boost technical titles and skills like ML Engineer, AI Engineer, vector search, Milvus, FAISS, NDCG, and Python.",
            ],
        ),
        (
            "Structured And Behavioral Scoring",
            [
                "Reward 5-9 year candidates with product-company history, India/Tier-1 location fit, hybrid readiness, and short notice period.",
                "Use recruiter response rate, activity, verification, interview completion, and open-to-work signals as availability modifiers.",
                "Add a plausibility layer to reduce honeypot and trap-profile risk.",
            ],
        ),
        (
            "Reasoning Generation",
            [
                "Each row gets a short justification grounded only in candidate facts: title, years, matched skills, location, and signals.",
                "Top rows stay positive and specific; weaker rows mention the actual concern instead of generic praise.",
                "This supports manual review without hallucinating skills not present in the profile.",
            ],
        ),
        (
            "Reproducibility",
            [
                "The repo includes a streaming generator for the submission CSV and a simple PDF deck writer.",
                "No external APIs are used during ranking, so the pipeline is reproducible in the sandboxed environment.",
                f"Deck output: {summary.get('deck', 'deck.pdf')}.",
            ],
        ),
    ]
