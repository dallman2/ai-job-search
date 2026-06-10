CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    company TEXT NOT NULL DEFAULT '',
    source TEXT,
    location TEXT DEFAULT '',
    salary TEXT DEFAULT '',
    description_md TEXT,
    description_text TEXT,
    fit_rating TEXT NOT NULL DEFAULT 'unrated'
        CHECK (fit_rating IN ('unrated', 'high', 'medium', 'low')),
    status TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'evaluated', 'skipped', 'applied')),
    evaluation_score INTEGER,
    first_seen TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    applied_date TEXT,
    notes TEXT,
    dedup_key TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_fit_rating ON jobs(fit_rating);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_dedup_key ON jobs(dedup_key);
CREATE INDEX IF NOT EXISTS idx_jobs_first_seen ON jobs(first_seen);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_evaluation_score ON jobs(evaluation_score);

CREATE VIRTUAL TABLE IF NOT EXISTS jobs_fts USING fts5(
    title, company, description_text, location,
    content='jobs', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS jobs_ai AFTER INSERT ON jobs BEGIN
    INSERT INTO jobs_fts(rowid, title, company, description_text, location)
    VALUES (new.id, new.title, new.company, new.description_text, new.location);
END;

CREATE TRIGGER IF NOT EXISTS jobs_ad AFTER DELETE ON jobs BEGIN
    INSERT INTO jobs_fts(jobs_fts, rowid, title, company, description_text, location)
    VALUES ('delete', old.id, old.title, old.company, old.description_text, old.location);
END;

CREATE TRIGGER IF NOT EXISTS jobs_au AFTER UPDATE ON jobs BEGIN
    INSERT INTO jobs_fts(jobs_fts, rowid, title, company, description_text, location)
    VALUES ('delete', old.id, old.title, old.company, old.description_text, old.location);
    INSERT INTO jobs_fts(rowid, title, company, description_text, location)
    VALUES (new.id, new.title, new.company, new.description_text, new.location);
END;

CREATE TABLE IF NOT EXISTS scrape_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('fast', 'deep', 'new')),
    strategies TEXT,
    companies_checked INTEGER DEFAULT 0,
    jobs_found INTEGER DEFAULT 0,
    jobs_new INTEGER DEFAULT 0,
    strategies_failed TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    skill TEXT NOT NULL,
    PRIMARY KEY (job_id, skill)
);

CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill);
