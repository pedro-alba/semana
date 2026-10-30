# Data Model: Accounts and weekly core

SQLite on the server (R2) and IndexedDB on the client (R5). Conventions:

- **Ids**: ids of user entities are text UUIDs, generated on the client. Session and token ids are the SHA-256 of the secret.
- **Moments**: ISO 8601 text in UTC (`2026-10-27T12:00:00Z`).
- **Weeks**: ISO date of the Monday (`2026-10-26`), in the account's time zone (R14).
- **Isolation**: **every data table has `account_id`** and every query filters by it, including in child tables. This is the rule checked by the isolation test (principle IV, SC-005).
- **Account deletion**: every foreign key to `account` uses `ON DELETE CASCADE`, so deleting the account erases everything (FR-006).

## Tables

### account

| Field | Type | Rules |
| --- | --- | --- |
| id | TEXT PK | UUID generated on the server |
| email | TEXT | unique, `COLLATE NOCASE`, no leading or trailing spaces |
| password_hash | TEXT | `scrypt$n$r$p$salt$hash` (R8) |
| timezone | TEXT | valid IANA name (R14) |
| processed_week | TEXT | last closed week already processed by the rollover. At sign-up, the Monday before the current week |
| created_at | TEXT | |

The rollover state is the `processed_week` column, with no table of its own.

### session

| Field | Type | Rules |
| --- | --- | --- |
| token_hash | TEXT PK | SHA-256 of the cookie token |
| account_id | TEXT FK → account | cascade |
| created_at | TEXT | |
| used_at | TEXT | updated at most once per hour. The session is valid if `used_at` is more recent than 30 days ago (FR-002) |

### password_token

| Field | Type | Rules |
| --- | --- | --- |
| token_hash | TEXT PK | |
| account_id | TEXT FK → account | cascade |
| expires_at | TEXT | creation + 1 h |
| used_at | TEXT NULL | single use. Filled in when the password is reset (FR-003) |

### login_attempt

Records only failures; the limits are in R9.

| Field | Type | Rules |
| --- | --- | --- |
| id | INTEGER PK | |
| email | TEXT | lowercase |
| ip | TEXT | |
| at | TEXT | records older than 7 days are removed |

### project

| Field | Type | Rules |
| --- | --- | --- |
| id | TEXT PK | |
| account_id | TEXT FK → account | cascade |
| name | TEXT | required, 1–60 characters after trimming leading and trailing spaces (FR-012) |
| created_at | TEXT | the project list is ordered by `created_at` and then by `rowid` |

A new account gets "Personal" and "Work", in that order (FR-007). Renaming and deleting projects are out of scope.

### task

| Field | Type | Rules |
| --- | --- | --- |
| id | TEXT PK | |
| account_id | TEXT FK → account | cascade |
| project_id | TEXT FK → project | cascade. The project must belong to the same account |
| week | TEXT | changes only through the rollover (FR-027) |
| title | TEXT | plain text, up to 500 characters |
| title_rev | INTEGER | starts at 0 (R7) |
| notes | TEXT | sanitized HTML (R11), up to 1 MB |
| notes_rev | INTEGER | starts at 0 |
| important | INTEGER | 0 or 1 |
| progress | INTEGER | `CHECK (progress BETWEEN 0 AND 100)` |
| position | INTEGER | position within (project, week). The group comes from the progress |
| weeks_open | INTEGER | starts at 1 and grows with each carry-over. The card shows "↪ week N" when it is greater than 1 (FR-020) |
| created_at | TEXT | |
| updated_at | TEXT | for "Worth picking up" (FR-051): changes with title, notes, progress, importance and any subtask operation. Does not change with reordering or with the rollover |

Index: `(account_id, project_id, week, position)`.

### subtask

| Field | Type | Rules |
| --- | --- | --- |
| id | TEXT PK | |
| account_id | TEXT FK → account | cascade |
| task_id | TEXT FK → task | cascade |
| text | TEXT | plain text, 1–500 characters, never empty (FR-039) |
| text_rev | INTEGER | starts at 0 |
| created_at | TEXT | pending ones are ordered by `created_at` |
| done_at | TEXT NULL | NULL = pending. Filled in = done, and the subtask shows up in the log with that date |

### log_entry

Stores carry-overs. Completed subtasks show up in the log from `subtask.done_at`, interleaved by date (FR-040).

| Field | Type | Rules |
| --- | --- | --- |
| id | TEXT PK | |
| account_id | TEXT FK → account | cascade |
| task_id | TEXT FK → task | cascade |
| at | TEXT | |
| kind | TEXT | `system` or `note`. This feature only writes `system` |
| text | TEXT | e.g. "Carried over from the week of 2026-10-19" |

### week_notes

| Field | Type | Rules |
| --- | --- | --- |
| account_id | TEXT FK → account | cascade |
| project_id | TEXT FK → project | cascade |
| week | TEXT | |
| html | TEXT | sanitized HTML. Empty is treated as a non-existent block: it does not appear in reads or exports. The row stays only to preserve `rev` (FR-052) |
| rev | INTEGER | no row = rev 0 |

PK: `(account_id, project_id, week)`.

### snapshot

| Field | Type | Rules |
| --- | --- | --- |
| account_id | TEXT FK → account | cascade |
| week | TEXT | |
| tasks | TEXT | JSON with the full copy of the week's tasks at closing time, across all projects: `task` fields, subtasks and log. It is immutable and survives task deletion (FR-034) |

PK: `(account_id, week)`. It is written once per processed week, only if the week had tasks.

## State transitions

**Week**, relative to the account's current week:

- **Future**: PLANNING label, editable.
- **Current**: no label, editable.
- **Past**: PAST label. The interface shows the snapshot and the week notes as read-only (FR-014, FR-048).

**Task:**

- **Open**: progress < 100.
- **Done**: progress = 100.
- **On entering a group** (created, completed or reopened): `position = max(position in the project's week) + 1`, which puts it at the end of the target group (FR-024).
- **On rollover**: the open tasks of `w` go to `w + 7` with `position` from 1 to k in the order they were in. Those already in `w + 7` add k (R12).
- **Delete**: erases the task, its subtasks and its log (cascade). Snapshots do not change.
- **Blank**: no title, notes, subtasks, progress or importance. The client sends `task.delete` when the person leaves it (FR-028).

**Subtask:**

- **Pending → done**: fills in `done_at`.
- **Done → pending**: clears `done_at`.
- **Undo the deletion**: a new `subtask.create` with the same id and the original fields.

**Session:**

- **Active**: `used_at` within 30 days.
- **Expired** through inactivity, or **deleted** on logout or on password reset (which deletes all of the account's sessions).

## Client (IndexedDB, `semana` database)

| Store | Key | Contents |
| --- | --- | --- |
| `cache` | `[account_id, key]` | latest response from `/api/start` (`key = "start"`) and from each `/api/week` (`key = "week|<project>|<monday>"`), with the pending local changes already applied |
| `queue` | autoincrement | `{account_id, op}`, in the order it was made (FR-056) |

Rules:

- Only the queue of the session's account is sent. If another account logs in on the same device, the previous one's pending changes are neither shown nor sent (FR-058).
- Logging out erases that account's `cache` and `queue`, after the confirmation when there are pending changes (FR-058, US1 scenario 5).
- When the session expires, nothing is erased. The queue is sent after the same account logs in again (FR-059).
- The `base_rev` value comes from the `cache` at send time. Each `ok` from the server updates the revision in the cache (R7).
