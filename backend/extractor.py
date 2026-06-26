"""Résumé extraction into the fixed schema.

The model's only job is to turn résumé text into ``ResumeData``. It never
designs pages or invents fields. In production, use OpenAI or Anthropic via an
API key. For local demos without a key, a small heuristic fallback extracts the
obvious fields so templates can still be tested end-to-end.
"""

from __future__ import annotations

import json
import os
import re

from pydantic import ValidationError

from .schemas import Contact, Education, Experience, Profile, ResumeData, SkillGroup, Stat

OPENAI_MODEL = "gpt-4.1-mini"
ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"

SYSTEM_PROMPT = """\
You convert résumé text into a fixed JSON structure. You are an extractor, not a \
writer or a web designer.

Rules:
- Only use information present in the résumé text. Do not invent employers, \
dates, degrees, metrics, or links.
- If a field is unknown, use an empty string or empty list — never guess.
- Preserve original job titles, school names, dates, and technical keywords \
verbatim.
- Keep quantified results ("reduced latency by 40%") in the achievement bullets.
- The summary may be lightly rewritten for flow, but every claim in it must be \
supported by the résumé.
- For `stats`, pick at most 4 of the most impressive quantified achievements \
already present in the résumé (e.g. coverage %, latency wins, dataset scores).
- For `contacts`, set `href` to mailto: for email, tel: for phone, and a full \
https:// URL for links. Leave `href` empty for a plain location.
- Choose `focus_tags` (3-6) that summarize the person's specialties.
"""


class ExtractionError(Exception):
    """Raised when the model is unavailable or returns no usable result."""


def extract_resume(text: str, *, api_key: str | None = None) -> ResumeData:
    """Extract structured résumé data from raw text.

    Provider priority:
    1. OpenAI when ``OPENAI_API_KEY`` is set.
    2. Anthropic when ``ANTHROPIC_API_KEY`` is set.
    3. Heuristic fallback for offline demos and tests.
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if key:
        return _extract_openai(text, key)

    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return _extract_anthropic(text, key)

    return _extract_heuristic(text)


def _json_schema() -> dict:
    schema = ResumeData.model_json_schema()
    # Some model APIs are happier when the root title is short and stable.
    schema["title"] = "ResumeData"
    return schema


def _parse_json_payload(payload: str) -> ResumeData:
    try:
        return ResumeData.model_validate_json(payload)
    except ValidationError as exc:
        raise ExtractionError(f"Model returned invalid résumé JSON: {exc}") from exc


def _extract_openai(text: str, api_key: str) -> ResumeData:
    """Extract with OpenAI structured outputs."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    try:
        response = client.responses.create(
            model=os.environ.get("OPENAI_MODEL", OPENAI_MODEL),
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "Extract this résumé into the required structure.\n\n"
                    "=== RÉSUMÉ TEXT ===\n"
                    + text,
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "resume_data",
                    "schema": _json_schema(),
                    "strict": True,
                }
            },
        )
    except Exception as exc:  # noqa: BLE001
        raise ExtractionError(f"OpenAI API error: {exc}") from exc

    output_text = getattr(response, "output_text", "") or ""
    if not output_text:
        raise ExtractionError("OpenAI did not return résumé JSON.")
    return _parse_json_payload(output_text)


def _extract_anthropic(text: str, api_key: str) -> ResumeData:
    """Extract with Anthropic JSON mode prompt discipline."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", ANTHROPIC_MODEL),
            max_tokens=8000,
            system=SYSTEM_PROMPT
            + "\nReturn only valid JSON matching this JSON Schema:\n"
            + json.dumps(_json_schema(), ensure_ascii=False),
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Extract this résumé into the required structure.\n\n"
                        "=== RÉSUMÉ TEXT ===\n" + text
                    ),
                }
            ],
        )
    except anthropic.APIError as exc:
        raise ExtractionError(f"Anthropic API error: {exc}") from exc

    if response.stop_reason == "refusal":
        raise ExtractionError("The model declined to process this document.")

    chunks = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            chunks.append(block.text)
    output_text = "\n".join(chunks).strip()
    if output_text.startswith("```"):
        output_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", output_text, flags=re.S)
    if not output_text:
        raise ExtractionError("Anthropic did not return résumé JSON.")
    return _parse_json_payload(output_text)


SECTION_HEADERS = {
    "education",
    "experience",
    "work experience",
    "professional experience",
    "project experience",
    "projects",
    "publications",
    "technical skills",
    "skills",
    "awards",
}


def _extract_heuristic(text: str) -> ResumeData:
    """Limited local fallback for demos without an LLM API key."""
    lines = [_clean_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line and not _is_noise_line(line)]
    first = _guess_name(lines)
    name = re.sub(r"[^A-Za-z\u4e00-\u9fff .'-]", "", first).strip() or first

    email = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    phone = re.search(r"(?:\+\d[\d ()-]{7,}\d|\(\d{3}\)\s*\d{3}[- ]\d{4})", text)
    location = ""
    header_text = " | ".join(lines[:4])
    if "|" in header_text:
        parts = [p.strip() for p in header_text.split("|")]
        for part in parts:
            if part.lower() == name.lower():
                continue
            if email and email.group(0) in part:
                continue
            if phone and phone.group(0) in part:
                continue
            if part and part != name:
                location = part
                break

    contacts: list[Contact] = []
    if email:
        contacts.append(
            Contact(type="email", label="Email", value=email.group(0), href=f"mailto:{email.group(0)}")
        )
    if phone:
        clean_phone = re.sub(r"[^\d+]", "", phone.group(0))
        contacts.append(
            Contact(type="phone", label="Phone", value=phone.group(0), href=f"tel:{clean_phone}")
        )
    if location:
        contacts.append(Contact(type="location", label="Location", value=location, href=""))

    sections = _split_sections(lines)
    education = _parse_education(sections.get("education", []))
    experience = _parse_experience(
        sections.get("experience", [])
        + sections.get("work experience", [])
        + sections.get("professional experience", [])
    )
    projects = _parse_projects(sections.get("project experience", []) + sections.get("projects", []))
    publications = _parse_plain_items(sections.get("publications", []))
    awards = _parse_plain_items(sections.get("awards", []))
    skills = _parse_skills(sections.get("technical skills", []) + sections.get("skills", []))
    stats = _extract_stats(text)

    headline = _guess_headline(experience, skills)
    summary = _build_summary(name, headline, experience, projects, publications)
    focus_tags = _guess_focus_tags(skills, projects, experience)

    return ResumeData(
        profile=Profile(name=name, headline=headline, location=location, summary=summary),
        contact_note="Reachable by email or phone." if contacts else "",
        contacts=contacts,
        focus_tags=focus_tags,
        stats=stats,
        education=education,
        experience=experience,
        projects=projects,
        publications=publications,
        awards=awards,
        skills=skills,
    )


def _clean_line(line: str) -> str:
    return line.replace("\ufeff", "").strip()


def _is_noise_line(line: str) -> bool:
    return bool(re.fullmatch(r"-+\s*PAGE\s+\d+\s*-+", line, flags=re.I))


def _guess_name(lines: list[str]) -> str:
    for line in lines[:8]:
        if "@" in line or "|" in line or re.search(r"\d", line):
            continue
        letters = re.sub(r"[^A-Za-z]", "", line)
        if 2 <= len(line) <= 60 and letters and line.upper() == line:
            return line.title()
    for line in lines[:8]:
        if "@" not in line and "|" not in line and not re.search(r"\d", line) and len(line) <= 80:
            return line
    return "Unknown Name"


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = ""
    for line in lines:
        key = line.lower().strip(":")
        if key in SECTION_HEADERS:
            current = key
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    return sections


def _parse_education(lines: list[str]) -> list[Education]:
    items: list[Education] = []
    for line in lines:
        if "|" not in line and "University" not in line and "College" not in line:
            continue
        left, _, right = line.partition("|")
        period = _extract_period(line)
        degree = right.replace(period, "").strip(" -|") if right else ""
        items.append(Education(school=left.strip(), degree=degree, period=period, details=[]))
    return items


def _parse_experience(lines: list[str]) -> list[Experience]:
    items: list[Experience] = []
    current: Experience | None = None
    for line in lines:
        normalized = line.lstrip("•●- ").strip()
        if "|" in line and not line.startswith(("•", "●", "-")):
            if current:
                items.append(current)
            org, _, rest = line.partition("|")
            period = _extract_period(rest)
            role = rest.replace(period, "").strip(" -")
            current = Experience(
                organization=org.strip(" -"),
                role=role or "Experience",
                period=period,
                location="",
                bullets=[],
            )
        elif current and normalized:
            current.bullets.append(normalized)
    if current:
        items.append(current)
    return items


def _parse_projects(lines: list[str]) -> list:
    from .schemas import Project

    projects = []
    for line in lines:
        if "|" not in line:
            continue
        name, _, desc = line.partition("|")
        if name.lower().endswith("projects:"):
            continue
        tech = [part.strip() for part in desc.split(",") if part.strip()]
        projects.append(
            Project(
                name=name.strip(" -"),
                type="Project",
                description=desc.strip(),
                technologies=tech[:8],
                link="",
            )
        )
    return projects


def _parse_plain_items(lines: list[str]) -> list[str]:
    return [line.lstrip("•●- ").strip() for line in lines if line and not line.endswith(":")]


def _parse_skills(lines: list[str]) -> list[SkillGroup]:
    groups: list[SkillGroup] = []
    for line in lines:
        if ":" not in line:
            continue
        group, _, raw_items = line.partition(":")
        items = [item.strip() for item in raw_items.split(",") if item.strip()]
        if items:
            groups.append(SkillGroup(group=group.strip(), items=items))
    return groups


def _extract_period(line: str) -> str:
    match = re.search(
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+\d{4}\s*[-–]\s*(?:Present|Now|Current|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z.]*\s+\d{4}|\d{4})|\d{4}\s*[-–]\s*(?:Present|\d{4}))",
        line,
        flags=re.I,
    )
    return match.group(1) if match else ""


def _extract_stats(text: str) -> list[Stat]:
    stats = []
    for match in re.finditer(r"\b\d+(?:\.\d+)?%|\b\d+\+", text):
        value = match.group(0)
        start = max(0, match.start() - 80)
        end = min(len(text), match.end() + 80)
        label = re.sub(r"\s+", " ", text[start:end]).strip()
        stats.append(Stat(value=value, label=label[:90]))
        if len(stats) == 4:
            break
    return stats


def _guess_headline(experience: list[Experience], skills: list[SkillGroup]) -> str:
    if experience:
        return experience[0].role
    flat_skills = " ".join(item for group in skills for item in group.items).lower()
    if "python" in flat_skills or "java" in flat_skills:
        return "Software Engineer"
    return "Professional"


def _build_summary(
    name: str,
    headline: str,
    experience: list[Experience],
    projects: list,
    publications: list[str],
) -> str:
    parts = [f"{name} is a {headline}."]
    if experience:
        orgs = ", ".join(item.organization for item in experience[:3])
        parts.append(f"Experience includes work with {orgs}.")
    if projects:
        parts.append(f"Selected projects include {', '.join(p.name for p in projects[:3])}.")
    if publications:
        parts.append("Research output includes peer-reviewed publications.")
    return " ".join(parts)


def _guess_focus_tags(skills: list[SkillGroup], projects: list, experience: list[Experience]) -> list[str]:
    corpus = " ".join(
        [item for group in skills for item in group.items]
        + [p.name + " " + p.description for p in projects]
        + [e.role + " " + " ".join(e.bullets) for e in experience]
    ).lower()
    candidates = [
        ("AI Engineering", ["ai", "llm", "rag", "transformer"]),
        ("Full-stack Development", ["react", "next.js", "node", "typescript"]),
        ("Backend Systems", ["django", "spring", "api", "postgresql"]),
        ("Data Systems", ["mysql", "mongodb", "redis", "database"]),
        ("Research", ["publication", "research", "acl", "ieee"]),
    ]
    tags = [label for label, words in candidates if any(word in corpus for word in words)]
    return tags[:6] or ["Professional"]
