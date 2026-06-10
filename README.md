# AI Job Search

An AI-powered job application framework built on [opencode](https://opencode.ai). Fork it, fill in your profile, and let AI evaluate job postings, tailor your CV, write cover letters, and prepare you for interviews.

## What this is

A structured workflow that turns opencode into a full-stack job application assistant. The core workflow (self-profiling, fit evaluation, and the drafter-reviewer application pipeline) is **language- and country-agnostic**.

```
/setup          /scrape              /apply <url>
  |                |                     |
  v                v                     v
Fill in        Search job           Evaluate fit
your profile   boards               Score & recommend
  |                |                     |
  v                v                     v
Profile        Present matches      Draft CV + Cover Letter
files ready    with fit ratings     (LaTeX, tailored)
                   |                     |
                   v                     v
               Pick a match         Reviewer agent critiques
               -> /apply            -> Revise -> Final output
```

The framework encodes career guidance best practices, including structured evaluation criteria, forward-looking cover letter framing, and optional salary benchmarking.

### Architecture

```
opencode CLI
  ├── Skills (instruction sets)
  │   ├── job-application-assistant   # Profile, evaluation, CV/cover letter drafting
  │   ├── profile-setup               # Interactive profile population
  │   ├── job-scraper                 # Multi-board job search orchestration
  │   └── upskill                    # Skill gap analysis and learning plans
  ├── Agents (Danish job portal CLIs — reference implementations)
  │   ├── jobbank-search              # Akademikernes Jobbank
  │   ├── jobdanmark-search           # Jobdanmark.dk
  │   ├── jobindex-search             # Jobindex.dk
  │   └── jobnet-search               # Jobnet.dk
  ├── Obscura (headless browser MCP)  # Board scraping via Docker
  └── SQLite API (kind cluster)       # Job tracking persistence
       ├── db/client.py               # Zero-dependency CLI
       ├── db/main.py                 # FastAPI REST API
       └── k8s/                       # kind deployment manifests

Output:
  cv/main_<company>.tex               # moderncv/banking CV (lualatex)
  cover_letters/cover_<company>_<role>.tex  # cover.cls cover letter (xelatex)
```

### Job board coverage

The scraper skill supports two modes:

- **Direct board access** (via Obscura headless browser): Greenhouse, Ashby, Wellfound, Y Combinator jobs, Indeed, LinkedIn (authenticated)
- **Regional CLI tools**: Four Danish job portals included as reference implementations. The pattern is designed to be swapped for your local job boards.

## Prerequisites

- [opencode](https://opencode.ai) (CLI) — `npm install -g @anthropic-ai/claude-code`
- Python 3.10+
- [Bun](https://bun.sh) — for job search CLI tools (skip if not using Danish portals)
- LaTeX distribution with `lualatex` and `xelatex`: [TeX Live](https://tug.org/texlive/) or [MiKTeX](https://miktex.org/)
- [Docker](https://docker.com) — for Obscura headless browser MCP server
- [kind](https://kind.sigs.k8s.io/) + [kubectl](https://kubernetes.io/docs/tasks/tools/) — for SQLite job tracking database

## Quick start

### 1. Fork and clone

```bash
gh repo fork dallman2/ai-job-search --clone
cd ai-job-search
```

### 2. Install job search tools (optional — skip if not in Denmark)

```bash
for tool in jobbank-search jobdanmark-search jobindex-search jobnet-search; do
  cd .agents/skills/$tool/cli && bun install && cd ../../../..
done
```

These CLIs are reference implementations for the Danish market. Build equivalent tools for your local job boards using the same structure.

### 3. Start infrastructure

```bash
# Start SQLite API on kind
cd db && bash start-cluster.sh && cd ..
python3 db/client.py health          # Should return {"status": "ok"}

# Pull and verify Obscura (headless browser for board scraping)
docker pull h4ckf0r0day/obscura
```

### 4. Set up your profile

```bash
opencode
# Then ask opencode:
"Set up my job search profile"
```

opencode will offer two paths: import your existing CV, or answer structured interview questions. See [SETUP.md](SETUP.md) for details.

### 5. Search and apply

```bash
"scrape jobs fast"                   # Search job boards autonomously
"evaluate this job: <url>"           # Score a specific posting
"draft CV and cover letter for it"   # Generate tailored LaTeX documents
```

## File structure

```
ai-job-search/
├── OPENDOC.md                         # Candidate profile (you populate via /setup)
├── SETUP.md                           # Detailed setup guide
├── CONTRIBUTING.md                    # How to contribute
├── .opencode/
│   └── skills/
│       ├── job-application-assistant/  # Core application skill
│       │   ├── SKILL.md               # Skill definition
│       │   └── 01-07-*.md             # Profile and template files (placeholders)
│       ├── job-scraper/SKILL.md        # Job search orchestration
│       ├── profile-setup/             # Interactive profile population
│       ├── upskill/                   # Skill gap analysis
│       └── customize-opencode/        # opencode configuration
├── .agents/skills/                    # Regional job portal CLIs
│   ├── jobbank-search/                # Akademikernes Jobbank (Denmark)
│   ├── jobdanmark-search/             # Jobdanmark.dk (Denmark)
│   ├── jobindex-search/               # Jobindex.dk (Denmark)
│   └── jobnet-search/                 # Jobnet.dk (Denmark)
├── cv/
│   └── main_example.tex               # moderncv LaTeX template (banking style)
├── cover_letters/
│   ├── cover.cls                      # Custom cover letter LaTeX class
│   └── OpenFonts/                     # Lato + Raleway fonts
├── db/
│   ├── Dockerfile                     # SQLite API container
│   ├── main.py                        # FastAPI REST API
│   ├── client.py                      # Zero-dependency CLI
│   ├── schema.sql                     # Database DDL
│   └── start-cluster.sh               # kind cluster startup
├── k8s/                               # kind deployment manifests
├── scripts/
│   ├── audit-personal-data.sh         # Personal data leak detector
│   └── push-to-public.sh              # Cherry-pick infrastructure to public
├── documents/
│   └── README.md                      # Folder layout for /setup data import
├── tools/
│   ├── convert_salary_excel.py        # Convert salary Excel to JSON
│   └── README_SALARY_TOOL.md
├── salary_lookup.py                   # Salary benchmarking tool
├── job_search_tracker.csv             # Application tracking (headers only)
└── LICENSE                            # MIT
```

## How `/apply` works

The `/apply` command runs a **drafter-reviewer workflow** with mandatory PDF compilation:

1. **Parse** the job posting (URL or text)
2. **Evaluate fit** against your profile (skills, experience, culture, location, career alignment)
3. **Draft** a tailored CV and cover letter in LaTeX
4. **Spawn a reviewer agent** that researches the company and critiques the drafts
5. **Revise** based on the reviewer's feedback
6. **Compile and inspect** both PDFs: lualatex for the CV, xelatex for the cover letter. The AI reads the rendered pages and iterates on the LaTeX until the CV is exactly 2 pages with no orphaned entry titles, and the cover letter fits exactly 1 page with consistent fonts.
7. **Present** the final output with a verification checklist

All claims are verified against your actual profile. The system never fabricates skills or experience.

### What makes this workflow different

- **PDF verification loop.** The workflow compiles and visually inspects every PDF and applies targeted fixes until the layout is clean.
- **Relevance-weighted CV cutting.** When a CV overflows 2 pages, lines are scored by relevance to the target posting, uniqueness, and cover-letter dependency — the lowest-scoring line is cut.
- **Drafter-reviewer separation.** A second agent critiques the drafts with fresh context, catching missed keywords, weak framing, and generic language.

## Customization

### Which files to edit

| File | What to change |
|------|---------------|
| `OPENDOC.md` | Your full profile (name, education, experience, skills) |
| `.opencode/skills/job-application-assistant/01-candidate-profile.md` | Structured CV data |
| `.opencode/skills/job-application-assistant/02-behavioral-profile.md` | Behavioral assessment |
| `.opencode/skills/job-application-assistant/04-job-evaluation.md` | Skill match areas, career goals |
| `.opencode/skills/job-application-assistant/05-cv-templates.md` | Profile statement templates |
| `.opencode/skills/job-application-assistant/07-interview-prep.md` | STAR examples |
| `.opencode/skills/job-scraper/search-queries.md` | Job search queries |

### LaTeX templates

The CV uses [moderncv](https://ctan.org/pkg/moderncv) (banking style). The cover letter uses a custom `cover.cls` with Lato/Raleway fonts. Replace these with your own templates by updating `05-cv-templates.md` and `06-cover-letter-templates.md`.

### Salary benchmarking

The salary tool works with any salary data you provide (union statistics, Glassdoor exports, personal research, etc.). See `tools/README_SALARY_TOOL.md` for the expected format. If you don't have salary data, the salary step is skipped.

### What's private

The `.gitignore` is pre-configured to protect your personal data. These are never committed:

- `data/` — your personal job tracking database
- `OPENDOC.md` — profile placeholders you fill in (keep your edited copy uncommitted)
- `.opencode/skills/job-application-assistant/01-07-*.md` — profile files with personal data
- `cv/main_*.tex`, `cover_letters/cover_*.tex` — generated application documents
- `documents/cv/`, `documents/linkedin/`, etc. — your source materials
- `salary_data.json` — your salary benchmark data

## Other commands

- **`/upskill`** analyzes skill gaps between your profile and tracked job postings. Produces a prioritized heatmap and learning plan with study resources.
- **`/setup`** can be re-run for specific sections (e.g., "Update my search queries").
- **`/reset`** wipes profile data to start fresh (requires explicit confirmation).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the dual-repo architecture and cherry-pick workflow used to keep personal data out of the public template.

## Acknowledgements

- [Mads Lorentzen](https://github.com/MadsLorentzen) — original framework (MIT License)
- [Mikkel Krogholm](https://github.com/mikkelkrogsholm) — Danish job search CLI skills
- [Obscura](https://github.com/h4ckf0r0day/obscura) — headless browser MCP server
- Built with [opencode](https://opencode.ai)

## License

MIT — see [LICENSE](LICENSE)
