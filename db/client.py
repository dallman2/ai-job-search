#!/usr/bin/env python3
r"""CLI client for the Job Search Database API.

Zero dependencies — uses only Python stdlib (urllib, json, argparse).
Default API URL: http://localhost:30080

Usage:
    python3 db/client.py health
    python3 db/client.py stats
    python3 db/client.py jobs list [--status STATUS] [--fit-rating RATING] [--source SRC] [--company NAME] [--since ISO] [--limit N] [--offset N]
    python3 db/client.py jobs get ID
    python3 db/client.py jobs search --q "keywords" [--limit N]
    python3 db/client.py jobs insert JSON_STRING
    python3 db/client.py jobs update ID [--status STATUS] [--fit-rating RATING] [--evaluation-score N] [--applied-date DATE] [--notes NOTES]
    python3 db/client.py jobs check [--url URL] [--dedup-key KEY]
    python3 db/client.py scrape-runs list [--limit N]
    python3 db/client.py scrape-runs log JSON_STRING
    python3 db/client.py skills aggregate [--status STATUSES]
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_API_URL = "http://localhost:30080"


def api_url(path: str) -> str:
    base = os.environ.get("API_URL", DEFAULT_API_URL)
    return f"{base.rstrip('/')}{path}"


def _get(path: str) -> dict:
    url = api_url(path)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def _post(path: str, data: dict) -> dict:
    url = api_url(path)
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode()
        print(f"HTTP {e.code}: {resp_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def _put(path: str, data: dict) -> dict:
    url = api_url(path)
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="PUT"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode()
        print(f"HTTP {e.code}: {resp_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def cmd_health():
    result = _get("/health")
    print(json.dumps(result, indent=2))


def cmd_stats():
    result = _get("/stats")
    print(json.dumps(result, indent=2))


def cmd_jobs_list(args):
    params = []
    if args.status:
        params.append(f"status={args.status}")
    if args.fit_rating:
        params.append(f"fit_rating={args.fit_rating}")
    if args.source:
        params.append(f"source={args.source}")
    if args.company:
        params.append(f"company={args.company}")
    if args.since:
        params.append(f"since={args.since}")
    params.append(f"limit={args.limit}")
    params.append(f"offset={args.offset}")
    if args.q:
        params.append(f"q={urllib.parse.quote(args.q)}")

    path = "/jobs?" + "&".join(params)
    result = _get(path)
    if isinstance(result, list):
        for job in result:
            print(json.dumps(job))
    else:
        print(json.dumps(result, indent=2))


def cmd_jobs_get(args):
    result = _get(f"/jobs/{args.id}")
    print(json.dumps(result, indent=2))


def cmd_jobs_search(args):
    params = [f"q={urllib.parse.quote(args.q)}", f"limit={args.limit}"]
    path = "/jobs/search?" + "&".join(params)
    result = _get(path)
    if isinstance(result, list):
        for job in result:
            print(json.dumps(job))
    else:
        print(json.dumps(result, indent=2))


def cmd_jobs_insert(args):
    try:
        data = json.loads(args.json_string)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    result = _post("/jobs", data)
    print(json.dumps(result, indent=2))


def cmd_jobs_update(args):
    updates = {}
    if args.status:
        updates["status"] = args.status
    if args.fit_rating:
        updates["fit_rating"] = args.fit_rating
    if args.evaluation_score is not None:
        updates["evaluation_score"] = args.evaluation_score
    if args.applied_date:
        updates["applied_date"] = args.applied_date
    if args.notes:
        updates["notes"] = args.notes
    if args.description_md:
        updates["description_md"] = args.description_md
    if args.description_text:
        updates["description_text"] = args.description_text

    if not updates:
        print("No update fields provided.", file=sys.stderr)
        sys.exit(1)

    result = _put(f"/jobs/{args.id}", updates)
    print(json.dumps(result, indent=2))


def cmd_jobs_check(args):
    params = []
    if args.url:
        params.append(f"url={urllib.parse.quote(args.url, safe='')}")
    if args.dedup_key:
        params.append(f"dedup_key={urllib.parse.quote(args.dedup_key, safe='')}")
    if not params:
        print("Must provide --url or --dedup-key", file=sys.stderr)
        sys.exit(1)
    path = "/jobs/check?" + "&".join(params)
    result = _get(path)
    print(json.dumps(result, indent=2))


def cmd_scrape_runs_list(args):
    path = f"/scrape-runs?limit={args.limit}"
    result = _get(path)
    print(json.dumps(result, indent=2))


def cmd_scrape_runs_log(args):
    try:
        data = json.loads(args.json_string)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    result = _post("/scrape-runs", data)
    print(json.dumps(result, indent=2))


def cmd_skills_aggregate(args):
    params = []
    if args.status:
        params.append(f"status={args.status}")
    path = "/jobs/skills/aggregate"
    if params:
        path += "?" + "&".join(params)
    result = _get(path)
    if isinstance(result, list):
        for job in result:
            print(json.dumps(job))
    else:
        print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="CLI client for the Job Search Database API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("health", help="Check API health")

    sub.add_parser("stats", help="Get aggregate job statistics")

    jobs = sub.add_parser("jobs", help="Job operations")
    jobs_sub = jobs.add_subparsers(dest="job_command")

    jobs_list = jobs_sub.add_parser("list", help="List jobs with filters")
    jobs_list.add_argument("--status", help="Filter by status (comma-separated)")
    jobs_list.add_argument("--fit-rating", help="Filter by fit rating (comma-separated)")
    jobs_list.add_argument("--source", help="Filter by source")
    jobs_list.add_argument("--company", help="Filter by company name (LIKE match)")
    jobs_list.add_argument("--since", help="Filter by first_seen > ISO timestamp")
    jobs_list.add_argument("--q", help="FTS5 full-text search query")
    jobs_list.add_argument("--limit", type=int, default=50)
    jobs_list.add_argument("--offset", type=int, default=0)

    jobs_get = jobs_sub.add_parser("get", help="Get a single job by ID")
    jobs_get.add_argument("id", type=int)

    jobs_search = jobs_sub.add_parser("search", help="Full-text search via FTS5")
    jobs_search.add_argument("--q", required=True, help="Search query")
    jobs_search.add_argument("--limit", type=int, default=20)

    jobs_insert = jobs_sub.add_parser("insert", help="Insert a new job")
    jobs_insert.add_argument("json_string", help="JSON string with job fields")

    jobs_update = jobs_sub.add_parser("update", help="Update a job by ID")
    jobs_update.add_argument("id", type=int)
    jobs_update.add_argument("--status", help="New status")
    jobs_update.add_argument("--fit-rating", help="New fit rating")
    jobs_update.add_argument("--evaluation-score", type=int, help="Evaluation score 0-100")
    jobs_update.add_argument("--applied-date", help="Application date (YYYY-MM-DD)")
    jobs_update.add_argument("--notes", help="Application notes")
    jobs_update.add_argument("--description-md", help="Full markdown description")
    jobs_update.add_argument("--description-text", help="Plaintext description")

    jobs_check = jobs_sub.add_parser("check", help="Check if a job URL/key exists")
    jobs_check.add_argument("--url", help="Job URL to check")
    jobs_check.add_argument("--dedup-key", help="Dedup key to check")

    scrape = sub.add_parser("scrape-runs", help="Scrape run operations")
    scrape_sub = scrape.add_subparsers(dest="scrape_command")

    scrape_list = scrape_sub.add_parser("list", help="List scrape runs")
    scrape_list.add_argument("--limit", type=int, default=10)

    scrape_log = scrape_sub.add_parser("log", help="Log a new scrape run")
    scrape_log.add_argument("json_string", help="JSON string with run fields")

    skills = sub.add_parser("skills", help="Skill operations")
    skills_sub = skills.add_subparsers(dest="skills_command")

    skills_agg = skills_sub.add_parser("aggregate", help="Get aggregated job data for skill analysis")
    skills_agg.add_argument("--status", help="Filter by statuses (comma-separated)")

    args = parser.parse_args()

    if args.command == "health":
        cmd_health()
    elif args.command == "stats":
        cmd_stats()
    elif args.command == "jobs":
        if args.job_command == "list":
            cmd_jobs_list(args)
        elif args.job_command == "get":
            cmd_jobs_get(args)
        elif args.job_command == "search":
            cmd_jobs_search(args)
        elif args.job_command == "insert":
            cmd_jobs_insert(args)
        elif args.job_command == "update":
            cmd_jobs_update(args)
        elif args.job_command == "check":
            cmd_jobs_check(args)
        else:
            jobs.print_help()
            sys.exit(1)
    elif args.command == "scrape-runs":
        if args.scrape_command == "list":
            cmd_scrape_runs_list(args)
        elif args.scrape_command == "log":
            cmd_scrape_runs_log(args)
        else:
            scrape.print_help()
            sys.exit(1)
    elif args.command == "skills":
        if args.skills_command == "aggregate":
            cmd_skills_aggregate(args)
        else:
            skills.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
