"""Canonical résumé data schema.

A single Pydantic schema that every résumé is parsed into and every template
renders from. Keeping the schema fixed is what stops "every résumé produces a
different website" — the LLM only fills these fields, it never invents new ones.

All fields are required so the structured-output extraction stays predictable;
"unknown" is represented by an empty string / empty list, never a missing key.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Profile(BaseModel):
    name: str = Field(description="Full name of the person.")
    headline: str = Field(
        description="Short professional title / target role, e.g. "
        "'Software Development Engineer'. One line, no trailing period."
    )
    location: str = Field(description="City, Country. Empty string if unknown.")
    summary: str = Field(
        description="2-4 sentence professional summary. May be rewritten for "
        "flow but must stay faithful to the résumé. Empty string if none."
    )


class Contact(BaseModel):
    type: str = Field(
        description="One of: email, phone, location, website, github, "
        "linkedin, scholar, other."
    )
    label: str = Field(description="Human label, e.g. 'Email', 'GitHub'.")
    value: str = Field(description="Display value, e.g. 'a@b.com'.")
    href: str = Field(
        description="Clickable URL: mailto:/tel:/https://. Empty if not linkable."
    )


class Stat(BaseModel):
    value: str = Field(description="Headline metric, e.g. '98%' or '13'.")
    label: str = Field(description="What the metric measures.")


class Education(BaseModel):
    school: str
    degree: str = Field(description="Degree and field of study.")
    period: str = Field(description="e.g. 'Aug. 2026 - Jul. 2028'.")
    details: list[str] = Field(
        default_factory=list,
        description="Optional honors, GPA, relevant coursework.",
    )


class Experience(BaseModel):
    organization: str
    role: str
    period: str = Field(description="e.g. 'Feb. 2026 - May 2026'.")
    location: str = Field(description="Empty string if unknown.")
    bullets: list[str] = Field(
        default_factory=list,
        description="Achievement bullets. Keep quantified results.",
    )


class Project(BaseModel):
    name: str
    type: str = Field(description="Short category, e.g. 'AI & Machine Learning'.")
    description: str
    technologies: list[str] = Field(default_factory=list)
    link: str = Field(description="Project URL. Empty string if none.")


class SkillGroup(BaseModel):
    group: str = Field(description="e.g. 'Languages', 'Frameworks'.")
    items: list[str]


class ResumeData(BaseModel):
    """The full structured résumé. Every template renders exactly this shape."""

    profile: Profile
    contact_note: str = Field(
        description="One short sentence inviting contact. Empty string if none."
    )
    contacts: list[Contact] = Field(default_factory=list)
    focus_tags: list[str] = Field(
        default_factory=list,
        description="3-6 short focus areas / specialties.",
    )
    stats: list[Stat] = Field(
        default_factory=list,
        description="0-4 standout quantified achievements pulled from the résumé.",
    )
    education: list[Education] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    publications: list[str] = Field(
        default_factory=list,
        description="Full citation strings, one per publication.",
    )
    awards: list[str] = Field(default_factory=list)
    skills: list[SkillGroup] = Field(default_factory=list)
