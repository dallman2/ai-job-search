---
name: upskill
description: Compares tracked job postings against the candidate profile to identify skill gaps and generate a prioritized learning plan with study resources. Triggers on: upskill, skill gaps, what should I learn, learning plan
---

# Upskill

Your purpose is to analyze skill gaps between the candidate's profile and tracked or targeted job postings, then produce a prioritized heatmap, a learning plan with study resources, and a recommended study order.

## Mode

- **Aggregate mode** (no URL provided): Analyze all evaluated and applied jobs in the database: `python3 db/client.py skills aggregate --status applied --status evaluated`. Use `evaluation_score` (0–100) for weighting where available; fall back to `fit_rating` mapping: high=80, medium=50, low=20, unrated=50. Lower scores mean the role exposed more gaps. Load the most recent `upskill/report-YYYY-MM-DD.md` for the "Since Last Report" diff.
- **Targeted mode** (URL or pasted text provided): Analyze only that posting via WebFetch. Do not load the database. Derive a slug from company+role for the report filename.

In both modes, read `.opencode/skills/job-application-assistant/01-candidate-profile.md` for current skills.

## Methodology

### Pass 1: Hard Skill Diff

In **aggregate mode**, query the database: `python3 db/client.py skills aggregate --status applied --status evaluated`. For each job, extract skills from `title` and `description_text` fields. Do not WebFetch — the `description_text` already contains the full job posting text in plaintext. Build a frequency map weighted by fit: `effective_score = evaluation_score if evaluation_score is not None else (80 if fit_rating=="high" else 50 if fit_rating=="medium" else 20 if fit_rating=="low" else 50)`. Then `weight = (100 - effective_score) / 100`. Lower-fit jobs contribute more weight. Rank gaps by score descending.

In **targeted mode**, extract required and preferred skills from the posting. Required skills before preferred; equal weight within each group.

**Diff against profile**: Remove any skill already present in the candidate profile. Be generous — if the profile mentions a skill in any form (e.g. "Python" covers "Python scripting"), remove it. What remains is the hard skill gap list.

### Pass 2: LLM Synthesis

Identify gaps the hard-skill diff misses, across four categories:
- **Domain knowledge**: Industry or problem-space familiarity (e.g. cybersecurity, climate tech)
- **Soft skills**: Communication styles, leadership expectations, ways of working
- **Tooling & process**: Frameworks, cloud services, methodologies (e.g. MLOps, CI/CD)
- **Credentials & certifications**: If postings list certifications as preferred or required

Tag each as `[domain]`, `[soft]`, `[tooling]`, or `[credential]`. Do not duplicate Pass 1 gaps.

## Output

### 1. Gap Heatmap

Combine Pass 1 and Pass 2 into a table:

| Priority | Skill / Area | Type | Gap Source |
|----------|-------------|------|------------|

Priority levels:
- **Critical**: High-frequency/weight hard skills, or domain gaps across most jobs
- **High**: Moderate scores, consistent soft/tooling gaps
- **Medium**: Lower-frequency hard skills, fewer-role synthesized gaps
- **Low**: One-off mentions or minor nice-to-haves

In targeted mode: required skills → Critical or High, preferred → Medium, synthesized → Medium or Low.

**Always print the heatmap before proceeding to the learning plan.**

### 2. Learning Plan

For every Critical and High gap (and Medium if fewer than 5 total gaps), produce:

1. **2–3 study resources** found via WebFetch. Prefer hands-on labs over lecture-only, official docs for tooling, books for domain. Include name, URL, and one-line rationale. Search with the current year.
2. **Tailored study direction**: What to skip given the candidate's existing background. Be specific about where to start.
3. **Realistic time estimate** (e.g. "~20h"). Err toward more rather than less.

Group entries under theme headings (e.g. Cloud & Infrastructure, Domain Knowledge, Soft Skills & Ways of Working). Omit Low-priority gaps from the learning plan.

### 3. Study Order

Number topics in recommended sequence. Rules:
- Dependencies first (if B requires A, place A before B and note it)
- Critical before High before Medium
- Quick wins (~5h) can go early for momentum
- Domain and soft skills last (study alongside practical projects)

Include a total estimated time.

### 4. Report Assembly

Assemble in order: header (mode, date), Since Last Report (aggregate only — gaps closed + new gaps vs previous report; omit if first report), Gap Heatmap, Learning Plan, Study Order.

**Save to file**: `upskill/report-YYYY-MM-DD.md` (aggregate) or `upskill/report-YYYY-MM-DD-<company>-<role>.md` (targeted, slugified: lowercase, spaces → hyphens, strip special chars). Always save — do not skip even if the user seems satisfied with terminal output.

## Rules

- Never fabricate resources. Only cite resources found via actual WebFetch results.
- Include the current year in resource searches so results stay fresh.
- Targeted mode ignores the database entirely — do not query `db/client.py skills aggregate`.
- Be generous with profile matching to avoid false-positive skill gaps.
