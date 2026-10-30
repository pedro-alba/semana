# API contract: Search

Conventions from the [001 contract](../../001-accounts-weekly-core/contracts/api.md).

## `GET /api/search`

No parameters. Responds only with data from the session's account.

```json
{
  "tasks": [
    {"id": "…", "project_id": "…", "week": "2026-10-26", "title": "Café with Joana",
     "notes": "<p>…</p>", "subtasks": ["Send agenda"], "progress": 40,
     "important": false, "due": null, "updated_at": "2026-10-27T12:00:00Z"}
  ],
  "notes": [{"project_id": "…", "week": "2026-10-19", "html": "<p>…</p>"}]
}
```

Does not run the rollover (each task's week comes as it is; the rollover already runs in `/api/start` when the app opens).
