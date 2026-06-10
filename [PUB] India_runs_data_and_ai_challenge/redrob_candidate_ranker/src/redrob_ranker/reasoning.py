from __future__ import annotations

from typing import Any


def _fmt_years(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _join_skill_list(skills: list[str]) -> str:
    if not skills:
        return ""
    if len(skills) == 1:
        return skills[0]
    if len(skills) == 2:
        return f"{skills[0]} and {skills[1]}"
    return f"{', '.join(skills[:-1])}, and {skills[-1]}"


def build_reasoning(candidate: dict[str, Any], signal: dict[str, Any]) -> str:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    title = profile.get("current_title", "")
    company = profile.get("current_company", "")
    years = float(signal.get("years", profile.get("years_of_experience", 0.0)))
    matched_skills = signal.get("matched_skills", []) or []
    location = profile.get("location", "")
    response = float(signals.get("recruiter_response_rate", 0.0))
    notice = int(signals.get("notice_period_days", 0) or 0)
    open_to_work = bool(signals.get("open_to_work_flag"))
    work_mode = str(signals.get("preferred_work_mode", ""))
    relocate = bool(signals.get("willing_to_relocate"))
    background = signal.get("title_pattern", "")
    penalty = float(signal.get("penalty_score", 0.0))

    positives: list[str] = []
    if background:
        positives.append(f"{_fmt_years(years)} years as a {title.lower()}")
    elif title:
        positives.append(f"{_fmt_years(years)} years in {title.lower()}")
    if company:
        positives.append(f"currently at {company}")
    if matched_skills:
        positives.append(f"hands-on with {_join_skill_list(matched_skills[:3])}")
    if open_to_work:
        positives.append("open to work")
    if work_mode:
        positives.append(f"prefers {work_mode} work")
    if location:
        positives.append(f"based in {location}")

    positive_sentence = "; ".join(positives[:3])
    if positive_sentence:
        positive_sentence = positive_sentence[0].upper() + positive_sentence[1:]

    concerns: list[str] = []
    if notice > 30:
        concerns.append(f"notice period is {notice} days")
    if response < 0.35:
        concerns.append(f"response rate is only {response:.2f}")
    if not relocate and location and "india" not in location.lower():
        concerns.append("relocation is not confirmed")
    if penalty < -0.15:
        concerns.append("background looks weaker for this JD")

    jd_link = "good fit for an embeddings/retrieval/ranking role"
    if matched_skills:
        jd_link = f"stronger on the JD because of {', '.join(matched_skills[:2])}"
    elif background:
        jd_link = f"aligned with the JD's technical depth through {background}"

    if concerns:
        concern_sentence = "; ".join(concerns[:2])
        return f"{positive_sentence}. {jd_link}; however, {concern_sentence}."
    return f"{positive_sentence}. {jd_link}."
