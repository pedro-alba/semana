# API contract: Calendar and due dates

The conventions of the [feature 001 contract](../../001-accounts-weekly-core/contracts/api.md) apply: JSON, session cookie, another account's data treated as nonexistent, and operations sent through `POST /api/ops`.

## Changes to existing routes

- **`GET /api/week`**: each task gains `"due": "2026-11-06" | null`. The same applies to the tasks in snapshots saved from this feature on. Old snapshots do not have the field, and the client treats it as `null` when missing.

## `GET /api/agenda?week=<monday>`

Runs the rollover before responding. Responds 422 if `week` is not a Monday.

```json
{
  "week": "2026-10-26",
  "events": [
    {
      "id": "…", "project_id": null, "title": "Team meeting",
      "start": "2026-10-06T09:00", "end": "2026-10-06T10:00", "all_day": false,
      "repeat": "weekly", "until": "2026-12-15",
      "location": "https://meet.example.com/abc", "description": "", "rev": 3
    }
  ],
  "dues": [
    {
      "task_id": "…", "project_id": "…", "week": "2026-10-19",
      "title": "Deliver report", "due": "2026-10-29",
      "progress": 40, "important": true
    }
  ]
}
```

- **`events`**: the account's candidate series ([data-model](../data-model.md#event-new-table)), across all projects. The client applies `occurrences`.
- **`dues`**:
  - the account's tasks with `week <= due < week + 7`, in any state, across all projects;
  - if `week` is the current week, also the tasks with `progress < 100` and `due < week` (overdue, FR-032);
  - each item's `week` field is the week the task is in, used to open it (FR-031).

## New operations in `POST /api/ops`

| `op` | Fields | Effect |
| --- | --- | --- |
| `task.due` | `id`, `value` (ISO date or `null`) | Sets or removes the due date. Last write wins. Updates `updated_at` (FR-005) |
| `event.save` | `id`, `project_id` (or `null`), `title`, `start`, `end`, `all_day`, `repeat`, `until` (or `null`), `location`, `description`, `base_rev` | Creates (`base_rev` 0) or updates under rule R3. Validates per R6. Responds `ok` with `rev`, or `conflict` with `{"value": <current event> | null, "rev": n}` |
| `event.delete` | `id` | Deletes the series. Idempotent |

The new isolation cases are `task.due`, `event.save` with another account's `project_id`, `event.save` and `event.delete` with another account's `id`, and `GET /api/agenda`, which never lists another account's data.
