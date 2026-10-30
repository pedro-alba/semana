# Data Model: Search

No new table or column. Search reads `task`, `subtask` and `week_notes`, always with `account_id = ?`.

## Search index (`GET /api/search` response, kept in the client cache under the key `search`)

| Field | Source |
| --- | --- |
| `tasks[]` | `id`, `project_id`, `week`, `title`, `notes` (HTML), `subtasks` (texts, pending and done), `progress`, `important`, `due`, `updated_at` |
| `notes[]` | `project_id`, `week`, `html`, only when `html` is not empty |

## Search item (client, not stored)

`{kind: 'task' | 'notes', id | key, title, body, week, projectId, at, t?}`, with `ft`/`fb` (title and body normalized by `fold`). Items from tasks and notes loaded in memory replace the index items with the same id or `week|project` key.
