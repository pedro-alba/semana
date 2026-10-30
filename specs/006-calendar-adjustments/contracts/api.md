# API contract: changes in 006

Conventions from the [001 contract](../../001-accounts-weekly-core/contracts/api.md). Only what changes relative to 002 and 003.

## `event.save`

- `repeat`: `"none" | "daily" | "weekly" | "monthly"`.
- `until`:
  - With `repeat` equal to `"none"`, it MUST be `null`.
  - For the others, it is optional: `null` means the recurrence does not end.

## `GET /api/agenda`

A series with no end date (null `until`, with a recurrence) is a candidate in any week after its start.

## `GET /api/search`

Gains `events`:

```json
"events": [{"id": "…", "project_id": null, "title": "Class", "start": "2026-10-27T19:00",
            "end": "2026-10-27T20:00", "all_day": false, "repeat": "weekly",
            "until": null, "location": "School", "description": ""}]
```
