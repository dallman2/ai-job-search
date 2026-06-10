# Setup Guide

Step-by-step instructions for getting the AI Job Search framework running.

## 1. Prerequisites

### opencode

Install the opencode CLI:

```bash
npm install -g @anthropic-ai/claude-code
```

See [opencode documentation](https://opencode.ai) for setup and configuration.

### Python

Python 3.10+ is required for the salary lookup tool and database client:

```bash
python3 --version
```

### Bun (for job search tools)

The Danish job portal CLIs are written in TypeScript and run with Bun:

```bash
curl -fsSL https://bun.sh/install | bash
```

If you're not searching in Denmark, skip this step. The CLIs are reference implementations — you can build equivalent tools for your local job boards.

### LaTeX

Install a LaTeX distribution to compile generated `.tex` files to PDF:

- **Windows:** [MiKTeX](https://miktex.org/download)
- **macOS:** [MacTeX](https://tug.org/mactex/)
- **Linux:** `sudo apt install texlive-full` or `sudo dnf install texlive-scheme-full`

The CV compiles with `lualatex` (pdflatex often fails on modern MiKTeX installs with `fontawesome5` font-expansion errors). The cover letter compiles with `xelatex` — `cover.cls` requires `fontspec` for its custom Lato/Raleway fonts.

### Docker

Required for the Obscura headless browser MCP server (used for job board scraping):

- **macOS:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Linux:** [Docker Engine](https://docs.docker.com/engine/install/)
- **Windows:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### kind + kubectl

Required for the SQLite job tracking database:

```bash
# macOS
brew install kind kubectl

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
# kubectl: https://kubernetes.io/docs/tasks/tools/

# Windows
choco install kind kubernetes-cli
```

## 2. Fork and clone

```bash
gh repo fork dallman2/ai-job-search --clone
cd ai-job-search
```

Or manually: fork on GitHub, then clone your fork.

## 3. Install job search CLI dependencies

```bash
for tool in jobbank-search jobdanmark-search jobindex-search jobnet-search; do
  cd .agents/skills/$tool/cli && bun install && cd ../../../..
done
```

**Skip this section if you are not searching in Denmark.** These CLIs demonstrate the pattern for building regional job board integrations. The scraper skill also supports direct board access via Obscura (Greenhouse, Ashby, Wellfound, LinkedIn, etc.) regardless of location.

## 4. Set up database infrastructure

The framework uses a SQLite database on a local Kubernetes (kind) cluster for job tracking persistence.

### Start the cluster

```bash
cd db && bash start-cluster.sh && cd ..
```

This creates a local kind cluster named `job-search-local`, builds the SQLite API Docker image, and deploys it with persistent storage.

### Verify it's running

```bash
python3 db/client.py health
# Should return: {"status": "ok", "db": "/data/job-search.db"}
```

The database file lives at `./data/job-search.db` on your filesystem (mounted into the kind cluster via `extraMounts`). It survives cluster teardown and is covered by `.gitignore`.

### Database CLI reference

```bash
python3 db/client.py stats                    # Aggregate job counts
python3 db/client.py jobs list --status new    # List jobs by status
python3 db/client.py jobs search --q "python"  # Full-text search
python3 db/client.py jobs insert '{"url": ..., "title": ..., ...}'  # Add a job
python3 db/client.py jobs update 42 --status applied --notes "..."   # Update a job
python3 db/client.py scrape-runs list          # View scrape run history
```

## 5. Set up Obscura (optional)

Obscura is a headless browser MCP server that enables the scraper to navigate job boards directly:

```bash
docker pull h4ckf0r0day/obscura
```

Verify it works:

```bash
docker run -i --rm --name obscura-test h4ckf0r0day/obscura mcp --stealth --help
```

The `opencode.json` config already includes the Obscura MCP server definition. If you prefer not to use Obscura, you can still use `/apply` by pasting job descriptions directly into chat.

## 6. Run the setup interview

Open the repository in opencode:

```bash
opencode
```

Then ask opencode to set up your profile:

> "Set up my job search profile"

opencode will offer two paths:

- **Path A (recommended):** Share your existing CV (mention the file or paste the text). opencode extracts your information and asks follow-up questions for anything missing.
- **Path B:** Answer structured interview questions section by section.

Both paths produce the same result: fully populated profile files.

### What gets populated

| File | Content |
|------|---------|
| `OPENDOC.md` | Your full candidate profile |
| `.opencode/skills/job-application-assistant/01-candidate-profile.md` | Structured education, experience, skills |
| `.opencode/skills/job-application-assistant/02-behavioral-profile.md` | Behavioral assessment |
| `.opencode/skills/job-application-assistant/04-job-evaluation.md` | Personalized skill match areas and career goals |
| `.opencode/skills/job-application-assistant/05-cv-templates.md` | Profile statement templates for your background |
| `.opencode/skills/job-application-assistant/07-interview-prep.md` | STAR examples from your experience |
| `.opencode/skills/job-scraper/search-queries.md` | Job search queries |

### Re-running setup

You can update specific sections later by asking opencode:

> "Update my skills section in the profile"
> "Update my experience section"
> "Reconfigure my job search queries"

Reconfiguring search queries re-runs the search configuration interview and suggests role types you may not have considered.

## 7. Optional: Set up salary benchmarking

If you have salary data (from a union, salary survey, Glassdoor, or personal research):

1. **Option A:** Create `salary_data.json` manually in the repo root (see `tools/README_SALARY_TOOL.md` for the format)
2. **Option B:** Convert from Excel:
   ```bash
   pip install openpyxl
   python3 tools/convert_salary_excel.py path/to/salary-data.xlsx --source "My Salary Data"
   ```

This creates `salary_data.json` which the application workflow uses for salary benchmarking. If you skip this step, salary lookup is simply omitted.

## 8. Test the workflow

Find a job posting you're interested in, then ask opencode:

> "Evaluate this job posting: [paste URL or job description]"

opencode will:
1. Evaluate the fit against your profile
2. Ask if you want to proceed
3. Draft a tailored CV and cover letter
4. Have a reviewer subagent critique the drafts
5. Revise and present the final output

## 9. Compile your documents

After the application workflow creates the LaTeX files:

```bash
# Compile CV
cd cv && lualatex main_<company>.tex && cd ..

# Compile cover letter
cd cover_letters && xelatex cover_<company>_<role>.tex && cd ..
```

## 10. What's private

Several files and directories in this repository will contain your personal data after setup. The `.gitignore` is pre-configured to protect all of them — they will never be committed or pushed.

### Files you edit (keep uncommitted)

- `OPENDOC.md` — your full profile (name, education, work history, behavioral traits, etc.)
- `.opencode/skills/job-application-assistant/01-candidate-profile.md` — structured CV data
- `.opencode/skills/job-application-assistant/02-behavioral-profile.md` — personality/trait assessment
- `.opencode/skills/job-application-assistant/03-writing-style.md` — tone preferences
- `.opencode/skills/job-application-assistant/04-job-evaluation.md` — career goals and evaluation criteria
- `.opencode/skills/job-application-assistant/05-cv-templates.md` — profile statement templates
- `.opencode/skills/job-application-assistant/06-cover-letter-templates.md` — cover letter templates
- `.opencode/skills/job-application-assistant/07-interview-prep.md` — STAR examples
- `.opencode/skills/job-scraper/search-queries.md` — your search queries
- `salary_data.json` — your salary benchmark data

### Directories that are fully gitignored

- `data/` — your personal SQLite job tracking database
- `documents/cv/`, `documents/linkedin/`, `documents/diplomas/`, `documents/references/`, `documents/applications/` — your source materials
- `applications/` — generated application documents for specific companies
- `postings/` — saved job postings

### Generated output files (gitignored)

- `cv/main_*.tex` — tailored CVs for specific roles
- `cover_letters/cover_*.tex` — tailored cover letters

All of these are covered by the `.gitignore`. You can verify your working tree is clean by running:

```bash
bash scripts/audit-personal-data.sh
```

## Troubleshooting

### "salary_data.json not found"
Expected if you haven't set up salary benchmarking. The application workflow skips this step automatically.

### Job search CLI tools not working
Make sure Bun is installed and you ran `bun install` in each CLI directory. These tools require network access.

### Database API not responding
Ensure the kind cluster is running:
```bash
kubectl --context kind-job-search-local get pods
kubectl --context kind-job-search-local port-forward service/sqlite-api 30080:8000
```
If the cluster doesn't exist, run `db/start-cluster.sh` again.

### LaTeX compilation errors
- CV: uses `lualatex` (pdflatex often fails on modern MiKTeX with `fontawesome5` font-expansion errors; lualatex handles the same sources cleanly)
- Cover letter: uses `xelatex` (for custom fonts in `OpenFonts/fonts/`)
- Make sure your LaTeX distribution includes the `moderncv` package

### Fonts not found in cover letter
The cover letter template expects fonts in `cover_letters/OpenFonts/fonts/`. Make sure this directory exists and contains the Lato and Raleway font files (they are included in the repository).
