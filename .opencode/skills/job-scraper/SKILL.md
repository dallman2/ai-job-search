---
name: job-scraper
description: Scrapes Danish job sites for new positions matching your profile. Deduplicates across runs. Triggers on: job scrape, find jobs, search jobs, new jobs, job search, scrape jobs
---

# Job Scraper

Your purpose is to search Danish job portals for new positions matching the candidate's profile, deduplicate against previously seen jobs, and present ranked results.

## Constraints

### State
- Before searching, load `job_scraper/seen_jobs.json` (create as `{"seen": {}}` if missing). Load `job_search_tracker.csv` to extract already-applied companies and roles. Know the deduplication keys upfront.
- Read `search-queries.md` (this directory) for the configured search strategy.

### Search
- Use the job portal CLI tools (jobindex-search, jobbank-search, jobnet-search, jobdanmark-search) for structured search. Target the configured geographic area and postings from the last 14 days.
- Run the top 3 priority categories from `search-queries.md` by default. Run all categories for a broad search. Prioritize a specific category if the user names a focus area.
- Use parallel tool calls across portals to speed up the search phase.

### Fetch & Deduplicate
- Pre-filter using titles and snippets before fetching. Do not WebFetch every result.
- For each promising result, use WebFetch to extract: title, company, location, posting date (or "recent"), URL, key requirements (brief), and application deadline if listed.
- Skip any URL or company+title combo already in `seen_jobs.json`. Skip any company+role already in `job_search_tracker.csv`. Skip postings with expired deadlines or marked as closed. Skip jobs requiring relocation or outside commute range.
- After fetching, add ALL jobs (new and skipped) to `seen_jobs.json` with title, company, URL, first_seen date, fit rating, and status (`new`/`skipped`/`evaluated`). Only present jobs not already in the seen list or tracker.

### Fit Assessment
- Rate each new job with a rapid signal (not the full evaluation in `04-job-evaluation.md`):
  - **High match**: Core skills directly involved.
  - **Medium match**: Adjacent experience.
  - **Low match**: Significant skill gaps.

### Output
- Present new jobs in a table sorted by fit (high first): Fit, Title, Company, Location, Deadline, URL.
- For each high-match job, add 2-3 bullets: why it matches, key requirements, any red flags.
- After presenting, ask: "Want me to evaluate any of these in detail? Just give me the number(s)."
- If the user picks a number, invoke the job-application-assistant skill for full evaluation.

### Rules
- Never fabricate job postings. Only present jobs found via actual search results.
- If the user decides to apply, add a row to `job_search_tracker.csv`.
