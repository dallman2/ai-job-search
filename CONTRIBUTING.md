# Contributing

## Dual-repo architecture

This project uses a dual-repo architecture to separate infrastructure (public) from personal data (private):

- **Public template** (`dallman2/ai-job-search`): The framework infrastructure — skills, CLIs, templates, database API, Kubernetes configs, documentation. This is what you forked. It contains no personal data.
- **Private fork**: The maintainer's working copy. Contains the public infrastructure plus personal data (profile, job tracking database, session cookies, tailored applications). Personal data lives in the working tree, protected by `.gitignore`, and is never committed.

```
Public template                     Private fork
(you fork this)                     (maintainer's working copy)
     │                                    │
     │  git clone / fork                  │  personal data in
     ▼                                    │  working tree only
  Your copy                               ▼
  (add your profile,                  Full history
   scrape, apply)                     cherry-picks infra
     │                                    │
     │  PRs welcome!                      │  scripts/push-to-public.sh
     ▼                                    ▼
  contribute back ───────────────────► Public template
  (infra only, no personal data)
```

## What belongs in the public repo

| Category | Examples | Public? |
|----------|---------|---------|
| Skill definitions | `SKILL.md` files | Yes |
| Profile templates | `01-candidate-profile.md` (placeholders) | Yes |
| LaTeX templates | `cv/main_example.tex`, `cover_letters/cover.cls` | Yes |
| Database API | `db/main.py`, `db/client.py`, `db/schema.sql` | Yes |
| Kubernetes configs | `k8s/deployment.yaml`, `k8s/kind-config.yaml` | Yes |
| CLI tools | `.agents/skills/*/` | Yes |
| Documentation | `README.md`, `SETUP.md`, `Docs/epics/` | Yes |
| Scripts | `scripts/audit-personal-data.sh`, `scripts/push-to-public.sh` | Yes |
| Your profile data | Filled-in `OPENDOC.md`, `01-candidate-profile.md` | **No** |
| Job database | `data/job-search.db` | **No** |
| Auth cookies | `.opencode/skills/job-scraper/cookies/` | **No** |
| Tailored applications | `cv/main_<company>.tex`, `cover_letters/cover_*.tex` | **No** |
| Scraper config | `frontier-rolodex.json`, custom `board-list.md` | **No** |

The `.gitignore` is pre-configured to block all personal data patterns. Run `scripts/audit-personal-data.sh` before any push to public.

## How to contribute (external contributors)

1. Fork the public template (`dallman2/ai-job-search`)
2. Make your changes — infrastructure only (skill improvements, bug fixes, new CLIs, docs)
3. Run the audit: `bash scripts/audit-personal-data.sh`
4. Open a pull request

Your PR must not contain personal data. The audit script will catch common patterns.

## How to contribute (maintainer)

The maintainer works in a private fork and cherry-picks infrastructure changes to the public template:

### 1. Develop in the private fork

Make changes as normal. Commit infrastructure changes separately from any personal data modifications.

### 2. Push to public

```bash
bash scripts/push-to-public.sh <commit-hash>
```

The script:
1. Fetches the latest public/main
2. Stashes local changes
3. Creates a temp branch off public/main
4. Cherry-picks the specified commit(s)
5. Runs `scripts/audit-personal-data.sh`
6. If audit passes → pushes to public/main
7. If audit fails → aborts, cleans up, exits with error

### 3. What to do if audit fails

The audit script found personal data in the cherry-picked changes. To fix:

1. Identify the file causing the failure (the audit output shows file paths)
2. Check out your original branch
3. Edit the file to remove personal data, or split the commit
4. Re-push with `scripts/push-to-public.sh <new-hash>`

### 4. Pushing multiple commits

```bash
# Push a range of commits (oldest..newest)
bash scripts/push-to-public.sh abc1234 def5678

# Push the latest commit on the current branch
bash scripts/push-to-public.sh HEAD
```

## The audit gate

`scripts/audit-personal-data.sh` checks for patterns that indicate personal data in the repository:

- Full names
- Personal email addresses
- Work email addresses (domain-specific)
- Phone numbers

It excludes the `Docs/epics/v1.3-open-source-release/` directory (planning documentation), the `scripts/` directory itself, and binary files.

**This script must pass before any push to the public repo.** It is the last line of defense against accidental data exposure.

## Conventions

### Placeholder pattern

Files that will contain personal data use `[PLACEHOLDER]` tokens in the committed version:

```
- **Name:** [YOUR_NAME]
- **Location:** [YOUR_CITY], [YOUR_COUNTRY]
```

Users replace these with their own data during `/setup`. Never commit real data to these files.

### opencode skill format

Skill files use the opencode skill format:

```markdown
---
name: skill-name
description: What the skill does
---

# Skill Title

Your purpose is to...
```

### LaTeX

- CV: `lualatex` (moderncv package, banking style)
- Cover letter: `xelatex` (`cover.cls` with fontspec for Lato/Raleway fonts)

### Database API

All database access goes through `db/client.py` — a zero-dependency CLI using only Python stdlib. Never use raw `sqlite3` or `curl` directly in skill instructions.

### AI tooling references

When mentioning agentic coding or AI tooling in generated CVs/cover letters, reference **opencode** by name.

## Project structure

See the file structure diagram in [README.md](README.md).
