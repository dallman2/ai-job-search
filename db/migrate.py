#!/usr/bin/env python3
"""Migrate jobs from seen_jobs.json to the SQLite database via the API.

Usage:
    python3 db/migrate.py [--api-url URL]

Reads job_scraper/seen_jobs.json, POSTs each job to the API, then POSTs
scrape run history. Handles 409 duplicates gracefully (idempotent).
Verifies row count at the end.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

DEFAULT_API_URL = os.environ.get("API_URL", "http://localhost:30080")


def api_url(path: str) -> str:
    base = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--api-url" else DEFAULT_API_URL
    # Also support --api-url passed inline:
    for i, arg in enumerate(sys.argv):
        if arg == "--api-url" and i + 1 < len(sys.argv):
            base = sys.argv[i + 1]
            break
    return f"{base.rstrip('/')}{path}"


def _post(path: str, data: dict) -> tuple:
    url = api_url(path)
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return True, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode()
        if e.code == 409:
            return False, resp_body
        print(f"  ERROR HTTP {e.code}: {resp_body}")
        return False, None
    except urllib.error.URLError as e:
        print(f"  ERROR Connection: {e.reason}")
        return False, None


def _get(path: str):
    url = api_url(path)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  ERROR GET: {e}")
        return None


def strip_markdown(md: str) -> str:
    """Basic markdown-to-plaintext for FTS5 indexing."""
    if not md:
        return ""
    text = md
    text = re.sub(r"#{1,6}\s+", "", text)
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`{1,3}[^`]+`{1,3}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def main():
    seen_path = "job_scraper/seen_jobs.json"
    if not os.path.exists(seen_path):
        print(f"ERROR: {seen_path} not found")
        sys.exit(1)

    with open(seen_path) as f:
        data = json.load(f)

    seen = data.get("seen", {})
    run_history = data.get("run_history", [])
    last_run = data.get("last_run")

    print(f"Loaded {len(seen)} jobs and {len(run_history)} scrape runs from {seen_path}")
    print(f"API: {api_url('/health')}")
    print()

    health = _get("/health")
    if not health or health.get("status") != "ok":
        print("ERROR: API not reachable")
        sys.exit(1)

    # Migrate jobs
    success = 0
    skipped = 0
    errors = 0

    for key, job in seen.items():
        title = job.get("title", "")
        company = job.get("company", "")
        url = job.get("url", "")
        description = job.get("description", "")

        payload = {
            "url": url,
            "title": title,
            "company": company if company else "",
            "source": job.get("source"),
            "location": job.get("location", ""),
            "salary": job.get("salary", ""),
            "description_md": description,
            "description_text": strip_markdown(description),
            "fit_rating": job.get("fit_rating", "unrated"),
            "status": job.get("status", "new"),
            "first_seen": job.get("first_seen", last_run or "2026-01-01T00:00:00Z"),
            "last_updated": job.get("first_seen", last_run or "2026-01-01T00:00:00Z"),
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        ok, result = _post("/jobs", payload)
        if ok:
            success += 1
            job_id = result.get("id", "?")
            print(f"  [{success}/{len(seen)}] + id={job_id} {company[:25]:<25} {title[:50]}")
        elif "already exists" in str(result):
            skipped += 1
            print(f"  [{success+skipped}/{len(seen)}] SKIP (already exists) {company[:25]:<25} {title[:50]}")
        else:
            errors += 1
            print(f"  [{success+skipped+errors}/{len(seen)}] ERROR {company[:25]:<25} {title[:50]}: {result}")

    print()
    print(f"Jobs: {success} migrated, {skipped} already existed, {errors} errors")

    # Migrate scrape runs
    run_ok = 0
    for run in run_history:
        payload = {
            "run_date": run.get("date"),
            "mode": run.get("mode", "fast"),
            "strategies": json.dumps(run.get("strategies", [])) if run.get("strategies") else None,
            "companies_checked": run.get("companies_checked", 0),
            "jobs_found": run.get("jobs_found", 0),
            "jobs_new": run.get("jobs_new", 0),
            "strategies_failed": json.dumps(run.get("strategies_failed", [])) if run.get("strategies_failed") else None,
        }
        payload["strategies"] = payload.get("strategies")
        payload["strategies_failed"] = payload.get("strategies_failed")
        ok, _ = _post("/scrape-runs", {k: v for k, v in payload.items() if v is not None})
        if ok:
            run_ok += 1

    print(f"Scrape runs: {run_ok} migrated")
    print()

    # Verify
    stats = _get("/stats")
    if stats:
        total = stats.get("total_jobs", 0)
        by_status = stats.get("by_status", {})
        by_fit = stats.get("by_fit_rating", {})
        print(f"DB total jobs: {total}")
        print(f"  by status: {by_status}")
        print(f"  by fit_rating: {by_fit}")

        expected = len(seen) + (skipped - success + success)  # total unique in source
        if total >= len(seen):
            print(f"\nOK: DB has {total} jobs, source had {len(seen)}")
        else:
            print(f"\nWARNING: DB has {total} jobs, but source had {len(seen)}")


if __name__ == "__main__":
    main()
