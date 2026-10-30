# Data Model: Calendar and due dates

Additions to the [feature 001 model](../001-accounts-weekly-core/data-model.md), in the migration `src/semana/migrations/002_calendar.sql` (now part of `migrations/001_initial.sql`). The same conventions apply: UUIDs generated on the client, `account_id` in every table and every query, and `ON DELETE CASCADE` to `account`.

## task (new column)

| Field | Type | Rules |
| --- | --- | --- |
| due | TEXT NULL | ISO date (`YYYY-MM-DD`) or NULL. Independent of `week` and kept by the rollover (FR-002). Included in `task_json` and therefore in the snapshot (FR-007) |

A task with a `due` is not "blank" (FR-006, client rule).

## event (new table)

| Field | Type | Rules |
| --- | --- | --- |
| id | TEXT PK | |
| account_id | TEXT FK → account | cascade |
| project_id | TEXT NULL FK → project | cascade. If given, from the same account |
| title | TEXT | 1–160 characters, trimmed |
| start | TEXT | `YYYY-MM-DDTHH:MM`, the account's local time (R5). For all-day, `T00:00` |
| end | TEXT | `> start` and at most `start + 31 days`. For all-day, `T00:00` of the day **after** the last one (exclusive) |
| all_day | INTEGER | 0 or 1 |
| repeat | TEXT | `CHECK (repeat IN ('none','weekly','monthly'))` |
| until | TEXT NULL | inclusive date. Required if `repeat <> 'none'`, NULL otherwise, and `>= date(start)` |
| location | TEXT | up to 500 characters. May be empty |
| description | TEXT | plain text, up to 10,000 characters. May be empty |
| rev | INTEGER | starts at 1 on create and is incremented on every write (R3) |
| created_at, updated_at | TEXT | |

Index: `event(account_id, start)`.

**Candidate series for a week `[s, s+7)`** (R2): `start < s+7` and one of these conditions:

- `end > s`, for one-off events and for the first occurrence;
- `repeat <> 'none' AND until >= s - 31 days`.

The exact cut is done on the client by `occurrences`.

**Event states:**

- **One-off**: `repeat = 'none'`.
- **Series**: with recurrence. Filling in `until` turns a one-off into a series, and clearing `until` turns the series into a one-off (FR-023).
- **Deleted**: deletes the row (the whole series).

## Client

- **Cache**: new key `agenda|<monday>`, holding the `GET /api/agenda` response with the pending local changes already applied.
- **Event adapter** (server → prototype format):

  ```
  {id, title, start, end, allDay: all_day,
   projectId: project_id || '', repeat,
   until: until || '', location, description, rev}
  ```

- **Task**: the adapter gains `due: due || ''`.
