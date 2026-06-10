import json
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

DB_PATH = os.environ.get("DB_PATH", "/data/job-search.db")

app = FastAPI(title="Job Search Database API")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.on_event("startup")
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path) as f:
            schema_sql = f.read()
        with get_db() as conn:
            conn.executescript(schema_sql)


def _make_dedup_key(company: str, title: str) -> str:
    combined = f"{company}_{title}"
    combined = combined.lower().strip()
    combined = re.sub(r"[^a-z0-9]+", "-", combined)
    combined = combined.strip("-")
    return combined


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


# ── Pydantic models ─────────────────────────────────────────────────────

class JobCreate(BaseModel):
    url: str
    title: str
    company: str = ""
    source: Optional[str] = None
    location: str = ""
    salary: Optional[str] = None
    description_md: Optional[str] = None
    description_text: Optional[str] = None
    fit_rating: str = "unrated"
    status: str = "new"
    first_seen: str
    last_updated: str


class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    description_md: Optional[str] = None
    description_text: Optional[str] = None
    fit_rating: Optional[str] = None
    status: Optional[str] = None
    evaluation_score: Optional[int] = None
    first_seen: Optional[str] = None
    applied_date: Optional[str] = None
    notes: Optional[str] = None


class ScrapeRunCreate(BaseModel):
    run_date: str
    mode: str
    strategies: Optional[str] = None
    companies_checked: int = 0
    jobs_found: int = 0
    jobs_new: int = 0
    strategies_failed: Optional[str] = None


# ── Health ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "db": DB_PATH}


# ── Stats ───────────────────────────────────────────────────────────────

@app.get("/stats")
def stats():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        by_status = {
            row["status"]: row["count"]
            for row in conn.execute(
                "SELECT status, COUNT(*) as count FROM jobs GROUP BY status"
            ).fetchall()
        }
        by_fit = {
            row["fit_rating"]: row["count"]
            for row in conn.execute(
                "SELECT fit_rating, COUNT(*) as count FROM jobs GROUP BY fit_rating"
            ).fetchall()
        }
        by_source = {
            row["source"] if row["source"] else "unknown": row["count"]
            for row in conn.execute(
                "SELECT source, COUNT(*) as count FROM jobs GROUP BY source"
            ).fetchall()
        }
        by_company = {
            row["company"] if row["company"] else "unknown": row["count"]
            for row in conn.execute(
                "SELECT company, COUNT(*) as count FROM jobs GROUP BY company ORDER BY count DESC LIMIT 10"
            ).fetchall()
        }
    return {
        "total_jobs": total,
        "by_status": by_status,
        "by_fit_rating": by_fit,
        "by_source": by_source,
        "by_company": by_company,
    }


# ── Jobs CRUD ───────────────────────────────────────────────────────────

@app.get("/jobs")
def list_jobs(
    status: Optional[str] = None,
    fit_rating: Optional[str] = None,
    source: Optional[str] = None,
    company: Optional[str] = None,
    since: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    with get_db() as conn:
        if q:
            rows = conn.execute(
                """
                SELECT jobs.*
                FROM jobs
                JOIN jobs_fts ON jobs.id = jobs_fts.rowid
                WHERE jobs_fts MATCH ?
                ORDER BY rank
                LIMIT ? OFFSET ?
                """,
                (q, limit, offset),
            ).fetchall()
            return [_row_to_dict(r) for r in rows]

        conditions = []
        params = []

        if status:
            statuses = [s.strip() for s in status.split(",")]
            placeholders = ",".join(["?" for _ in statuses])
            conditions.append(f"status IN ({placeholders})")
            params.extend(statuses)

        if fit_rating:
            ratings = [r.strip() for r in fit_rating.split(",")]
            placeholders = ",".join(["?" for _ in ratings])
            conditions.append(f"fit_rating IN ({placeholders})")
            params.extend(ratings)

        if source:
            conditions.append("source = ?")
            params.append(source)

        if company:
            conditions.append("company LIKE ?")
            params.append(f"%{company}%")

        if since:
            conditions.append("first_seen > ?")
            params.append(since)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        params.extend([limit, offset])

        rows = conn.execute(
            f"SELECT * FROM jobs {where} ORDER BY first_seen DESC LIMIT ? OFFSET ?",
            params,
        ).fetchall()

        return [_row_to_dict(r) for r in rows]


@app.get("/jobs/check")
def check_job(
    url: Optional[str] = None,
    dedup_key: Optional[str] = None,
):
    with get_db() as conn:
        if url:
            row = conn.execute("SELECT * FROM jobs WHERE url = ?", (url,)).fetchone()
            if row:
                return {"exists": True, "job": _row_to_dict(row)}
        if dedup_key:
            row = conn.execute(
                "SELECT * FROM jobs WHERE dedup_key = ?", (dedup_key,)
            ).fetchone()
            if row:
                return {"exists": True, "job": _row_to_dict(row)}
    return {"exists": False}


@app.get("/jobs/search")
def search_jobs(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT jobs.*, snippet(jobs_fts, 1, '<mark>', '</mark>', '...', 32) as snippet
            FROM jobs
            JOIN jobs_fts ON jobs.id = jobs_fts.rowid
            WHERE jobs_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (q, limit),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


@app.get("/jobs/{job_id}")
def get_job(job_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        return _row_to_dict(row)


@app.post("/jobs", status_code=201)
def create_job(job: JobCreate):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM jobs WHERE url = ?", (job.url,)
        ).fetchone()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Job with this URL already exists (id={existing['id']})",
            )

        if job.fit_rating not in ("unrated", "high", "medium", "low"):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid fit_rating: '{job.fit_rating}'. Must be one of: unrated, high, medium, low",
            )

        if job.status not in ("new", "evaluated", "skipped", "applied"):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status: '{job.status}'. Must be one of: new, evaluated, skipped, applied",
            )

        dedup_key = _make_dedup_key(job.company, job.title)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        cursor = conn.execute(
            """
            INSERT INTO jobs (url, title, company, source, location, salary,
                              description_md, description_text, fit_rating, status,
                              first_seen, last_updated, dedup_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.url,
                job.title,
                job.company,
                job.source,
                job.location,
                job.salary,
                job.description_md,
                job.description_text,
                job.fit_rating,
                job.status,
                job.first_seen,
                job.last_updated,
                dedup_key,
            ),
        )
        job_id = cursor.lastrowid

    return get_job(job_id)


@app.put("/jobs/{job_id}")
def update_job(job_id: int, updates: JobUpdate):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Job not found")

        fields = {}
        if updates.title is not None:
            fields["title"] = updates.title
        if updates.company is not None:
            fields["company"] = updates.company
        if updates.source is not None:
            fields["source"] = updates.source
        if updates.location is not None:
            fields["location"] = updates.location
        if updates.salary is not None:
            fields["salary"] = updates.salary
        if updates.description_md is not None:
            fields["description_md"] = updates.description_md
        if updates.description_text is not None:
            fields["description_text"] = updates.description_text
        if updates.fit_rating is not None:
            if updates.fit_rating not in ("unrated", "high", "medium", "low"):
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid fit_rating: '{updates.fit_rating}'",
                )
            fields["fit_rating"] = updates.fit_rating
        if updates.status is not None:
            if updates.status not in ("new", "evaluated", "skipped", "applied"):
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid status: '{updates.status}'",
                )
            fields["status"] = updates.status
        if updates.evaluation_score is not None:
            fields["evaluation_score"] = updates.evaluation_score
        if updates.first_seen is not None:
            fields["first_seen"] = updates.first_seen
        if updates.applied_date is not None:
            fields["applied_date"] = updates.applied_date
        if updates.notes is not None:
            fields["notes"] = updates.notes

        if not fields:
            return get_job(job_id)

        fields["last_updated"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        set_clauses = [f"{k} = ?" for k in fields]
        values = list(fields.values())
        values.append(job_id)

        conn.execute(
            f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = ?",
            values,
        )

    return get_job(job_id)


# ── Scrape Runs ─────────────────────────────────────────────────────────

@app.get("/scrape-runs")
def list_scrape_runs(limit: int = Query(default=10, ge=1, le=100)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM scrape_runs ORDER BY run_date DESC LIMIT ?", (limit,)
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


@app.post("/scrape-runs", status_code=201)
def create_scrape_run(run: ScrapeRunCreate):
    if run.mode not in ("fast", "deep", "new"):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid mode: '{run.mode}'. Must be one of: fast, deep, new",
        )
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO scrape_runs (run_date, mode, strategies, companies_checked,
                                     jobs_found, jobs_new, strategies_failed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.run_date,
                run.mode,
                run.strategies,
                run.companies_checked,
                run.jobs_found,
                run.jobs_new,
                run.strategies_failed,
            ),
        )
        run_id = cursor.lastrowid

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM scrape_runs WHERE id = ?", (run_id,)
        ).fetchone()
        return _row_to_dict(row)


# ── Skills Aggregate ────────────────────────────────────────────────────

@app.get("/jobs/skills/aggregate")
def skills_aggregate(
    status: Optional[str] = Query(default=None, description="Comma-separated statuses"),
):
    with get_db() as conn:
        if status:
            statuses = [s.strip() for s in status.split(",")]
            placeholders = ",".join(["?" for _ in statuses])
            rows = conn.execute(
                f"""
                SELECT id, title, company, description_text, evaluation_score, fit_rating
                FROM jobs
                WHERE status IN ({placeholders})
                ORDER BY first_seen DESC
                """,
                statuses,
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, title, company, description_text, evaluation_score, fit_rating
                FROM jobs
                WHERE status IN ('evaluated', 'applied')
                ORDER BY first_seen DESC
                """
            ).fetchall()
        return [_row_to_dict(r) for r in rows]
