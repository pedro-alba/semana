CREATE TABLE account (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    timezone TEXT NOT NULL,
    processed_week TEXT NOT NULL,
    created_at TEXT NOT NULL,
    appearance TEXT NOT NULL DEFAULT '{}',
    language TEXT NOT NULL DEFAULT 'auto' CHECK (language IN ('auto','en','pt-BR'))
);

CREATE TABLE session (
    token_hash TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    used_at TEXT NOT NULL
);

CREATE TABLE password_token (
    token_hash TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL,
    used_at TEXT NULL
);

CREATE TABLE login_attempt (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    ip TEXT NOT NULL,
    at TEXT NOT NULL
);

CREATE TABLE project (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE task (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    week TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    title_rev INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    notes_rev INTEGER NOT NULL DEFAULT 0,
    important INTEGER NOT NULL DEFAULT 0 CHECK (important IN (0,1)),
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    position INTEGER NOT NULL,
    weeks_open INTEGER NOT NULL DEFAULT 1,
    due TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE subtask (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    task_id TEXT NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    text_rev INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    done_at TEXT NULL
);

CREATE TABLE log_entry (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    task_id TEXT NOT NULL REFERENCES task(id) ON DELETE CASCADE,
    at TEXT NOT NULL,
    kind TEXT NOT NULL,
    text TEXT NOT NULL
);

CREATE TABLE week_notes (
    account_id TEXT NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    week TEXT NOT NULL,
    html TEXT NOT NULL,
    rev INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (account_id, project_id, week)
);

CREATE TABLE snapshot (
    account_id TEXT NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    week TEXT NOT NULL,
    tasks TEXT NOT NULL,
    PRIMARY KEY (account_id, week)
);

CREATE TABLE event (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    project_id TEXT REFERENCES project(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    start TEXT NOT NULL,
    "end" TEXT NOT NULL,
    all_day INTEGER NOT NULL DEFAULT 0 CHECK (all_day IN (0,1)),
    repeat TEXT NOT NULL DEFAULT 'none' CHECK (repeat IN ('none','daily','weekly','monthly')),
    until TEXT,
    location TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    fills_day INTEGER NOT NULL DEFAULT 0 CHECK (fills_day IN (0,1)),
    skipped TEXT NOT NULL DEFAULT '[]',
    rev INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE image (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    mime TEXT NOT NULL CHECK (mime IN ('image/jpeg','image/png','image/gif','image/webp')),
    data BLOB NOT NULL,
    size INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX task_week ON task(account_id, project_id, week, position);
CREATE INDEX subtask_task ON subtask(task_id);
CREATE INDEX log_entry_task ON log_entry(task_id);
CREATE INDEX login_attempt_email ON login_attempt(email);
CREATE INDEX event_start ON event(account_id, start);
CREATE INDEX image_account ON image(account_id);
