# Data Model: Prototype import and backup

No schema change. What is new is the file format.

## App backup file (version 1)

```json
{
  "format": "semana-backup",
  "version": 1,
  "exported_at": "2026-10-29T12:00:00Z",
  "processed_week": "2026-10-19",
  "projects": [{"id": "…", "name": "Personal", "created_at": "…"}],
  "tasks": [Task],
  "notes": [{"project_id": "…", "week": "2026-10-26", "html": "<p>…</p>"}],
  "events": [{"id": "…", "project_id": null, "title": "…", "start": "2026-10-27T09:00",
              "end": "2026-10-27T10:00", "all_day": false, "repeat": "weekly",
              "until": "2027-01-01", "location": "", "description": ""}],
  "snapshots": [{"week": "2026-10-19", "tasks": [Task]}]
}
```

**Task**:

```json
{"id": "…", "project_id": "…", "week": "2026-10-26", "title": "…", "notes": "<p>…</p>",
 "important": false, "progress": 40, "position": 0, "weeks_open": 1, "due": null,
 "created_at": "…", "updated_at": "…",
 "subtasks": [{"id": "…", "text": "…", "created_at": "…", "done_at": null}],
 "log": [{"id": "…", "at": "…", "kind": "system", "text": "…"}]}
```

## Validation rules (server)

The limits are the ops' limits (`ops.py`):

| Item | Rules |
| --- | --- |
| File | `format == "semana-backup"`; `version == 1` |
| projects | 1 or more; `name` with 1–60 characters; IDs unique in the file |
| tasks | `project_id` present in `projects`; `week` is a Monday; `title` ≤ 500; `notes` ≤ 1 MB; `progress` from 0 to 100; `weeks_open` ≥ 1; `due` a date or `null`; unique IDs |
| subtasks | `text` with 1–500 characters |
| log | `kind` is `system` or `note` |
| notes | `project_id` present in `projects`; `week` is a Monday; `html` ≤ 1 MB; one block per project + week pair |
| events | rules of `event.save` (002); a `project_id` not in `projects` becomes `null` |
| snapshots | `week` is a Monday; weeks equal to or after the current one are ignored; tasks with a `project_id` not in `projects` are dropped from the snapshot |
| dates and times | ISO 8601 with time zone, stored in the app's format (`clock.iso`) |

All HTML goes through `clean` (nh3). `position` is rebuilt as 1, 2, 3… within each project + week, in file order.

## From the prototype (v2) to the app (`fromPrototype`)

| Prototype | App |
| --- | --- |
| `week` (current processed week) | `processed_week = week - 7` |
| `projects[].name` | `projects[].name` (`created_at` = now) |
| `tasks[]` | `tasks[]`: `title→title`, `description→notes`, `important→important`, `progress→progress`, `order→position`, `carries+1→weeks_open`, `due→due` (empty → `null`), `createdAt→created_at`, `lastActivity→updated_at` |
| `subtasks[]` | `text`, `created_at`, `done_at` (`doneAt` if `done`, otherwise `null`) |
| `log[]` | `at`, `kind` (`system`, `note`: same values), `text` |
| `notes["week\|project"]` | `notes[]` |
| `events[]` | `events[]` (`repeat` `none/weekly/monthly` keeps its value, empty `until` → `null`, empty `projectId` → `null`) |
| `snapshots{week: tasks}` | `snapshots[]` |

The field mapping is the same as `fromAPI` and `toAPI` in `app.js`.
