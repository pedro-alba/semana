# API Contract: Accounts and weekly core

HTTP + JSON, served on the same origin as the client. The rationale for each choice is in [research.md](../research.md) and the fields in [data-model.md](../data-model.md).

## Conventions

- Request and response bodies in JSON (`Content-Type: application/json`). Requests that change data without that header get 415 (R8).
- The session goes in the `semana_session` cookie (`HttpOnly; Secure; SameSite=Lax; Path=/`).
- Every route under `/api`, except those marked **public**, responds 401 `{"error": "no_session"}` without a valid session.
- Data from another account is treated exactly like data that does not exist: 404 on reads and `not_found` on operations (FR-005).
- Errors follow the format `{"error": "<code>", ...details}`. User-facing texts live in the client.

## Accounts

### `POST /api/account` (public): sign-up

Body: `{"email": str, "password": str (≥ 8), "timezone": str (IANA)}`

| Status | Body |
| --- | --- |
| 201 | `{"account": {"id", "email", "timezone"}}` + session cookie. The account already comes with the Personal and Work projects (FR-007) |
| 409 | `{"error": "email_taken"}`. The client suggests recovering the password |
| 422 | `{"error": "invalid", "fields": [...]}` |

### `POST /api/login` (public)

Body: `{"email", "password"}`

| Status | Body |
| --- | --- |
| 200 | `{"account": {...}}` + cookie |
| 401 | `{"error": "credentials"}` |
| 429 | `{"error": "locked", "retry_at": iso}` (FR-004, R9) |

### `POST /api/logout`

Deletes the current session and the cookie. Responds 204.

### `POST /api/password/request` (public)

Body: `{"email"}`. **Always** responds 202 with an empty body. If the account exists, the e-mail is sent in the background with the link `<BASE_URL>/password#<token>` (R10).

### `POST /api/password/reset` (public)

Body: `{"token", "password"}`.

| Status | Body |
| --- | --- |
| 204 | Password changed and all of the account's sessions deleted. Does not create a session: the person logs in with the new password |
| 400 | `{"error": "invalid_token"}` when the token is expired, already used or does not exist |

### `DELETE /api/account`

Body: `{"password"}`.

| Status | Body |
| --- | --- |
| 204 | Account and all data deleted, cookie removed. The e-mail becomes free (FR-006) |
| 403 | `{"error": "wrong_password"}` |

## Reads

Both routes apply the rollover before responding (R12).

### `GET /api/start`

```json
{
  "account": {"id": "…", "email": "…", "timezone": "America/Sao_Paulo"},
  "current_week": "2026-10-26",
  "now": "2026-10-27T12:00:00Z",
  "projects": [{"id": "…", "name": "Personal"}, {"id": "…", "name": "Work"}]
}
```

### `GET /api/week?project=<id>&week=<monday>`

```json
{
  "week": "2026-10-26",
  "state": "current | planning | past",
  "tasks": [
    {
      "id": "…", "title": "…", "title_rev": 3,
      "notes": "<p>…</p>", "notes_rev": 7,
      "important": false, "progress": 40, "position": 2,
      "weeks_open": 2,
      "created_at": "…", "updated_at": "…",
      "subtasks": [{"id": "…", "text": "…", "text_rev": 0, "created_at": "…", "done_at": null}],
      "log": [{"id": "…", "at": "…", "kind": "system", "text": "Carried over from the week of 2026-10-19"}]
    }
  ],
  "notes": {"html": "<p>…</p>", "rev": 4}
}
```

- **`past` state**: `tasks` comes from the week's snapshot, filtered by project. It is empty if there is no snapshot.
- **Task order**: by `position`. The client splits open and done tasks by progress.
- **Project**: 404 `{"error": "not_found"}` if the project does not exist or belongs to another account.
- **Week**: 422 if `week` is not a Monday.
- **Overview**: the overview (FR-050) and "Worth picking up" (FR-051) are computed on the client from this response.

The client keeps the difference between `now` and its own clock and uses it in every time calculation: the rollover check every minute and the 72 hours of "Worth picking up". That way, a wrong clock on the device does not change the result, and the server's simulated clock (`SEMANA_NOW`) also applies on the client.

## Writes: `POST /api/ops`

```json
{
  "account_id": "<account that owns the queue>",
  "ops": [
    {"op": "task.create", "id": "…", "project_id": "…", "week": "2026-10-26"},
    {"op": "task.title", "id": "…", "value": "Review contract", "base_rev": 0}
  ]
}
```

- **Queue account**: if `account_id` differs from the session's account, the whole batch is refused with 409 `{"error": "wrong_account"}` and nothing is applied (FR-058).
- **Order**: operations are applied in batch order, and each one is atomic.
- **Size**: up to 200 operations per batch. The client sends the rest in following batches.
- **Response**: 200 `{"results": [{"status": "ok", ...}, ...]}`, one per operation, in the same order.

| `status` | Meaning | Client action |
| --- | --- | --- |
| `ok` | applied, or already applied (idempotency, R6). Text operations return `rev` | removes it from the queue and updates the `rev` in the cache |
| `conflict` | outdated `base_rev` and a different value. Returns the current `{"value", "rev"}` (FR-061, R7) | removes it from the queue and shows the notice with both versions |
| `not_found` | the target does not exist or belongs to another account | removes it from the queue. Counts as success if the operation was a deletion |
| `invalid` | failed validation. Returns `{"fields": [...]}` | removes it from the queue and shows "failed" in the footer (FR-055) |

### Operations

The server sanitizes every HTML field with `nh3` (R11) and trims leading and trailing spaces from plain texts. Operations marked "U" update `task.updated_at` (FR-051).

| `op` | Fields | Effect |
| --- | --- | --- |
| `project.create` | `id`, `name` | Creates the project. If the id already exists, nothing changes |
| `task.create` | `id`, `project_id`, `week` | Creates the task at 0%, at the end of the open tasks. If `week` is already closed, it goes to the current week (FR-027, R13). If the id already exists, nothing changes |
| `task.title` | `id`, `value`, `base_rev` | Text with revision (R7). U |
| `task.notes` | `id`, `value` (HTML), `base_rev` | Text with revision. U |
| `task.progress` | `id`, `value` (0–100) | When crossing 100 in either direction, the task goes to the end of the target group (FR-024, FR-025). U |
| `task.important` | `id`, `value` (bool) | U |
| `task.reorder` | `project_id`, `week`, `ids` (new order of a group) | Redistributes among the ids the positions they already hold. Missing ids stay where they are. Does not update `updated_at` (FR-023, FR-051) |
| `task.delete` | `id` | Deletes the task with its subtasks and log. Snapshots do not change (FR-034) |
| `subtask.create` | `id`, `task_id`, `text`, `created_at?`, `done_at?` | The optional fields are used to undo a deletion (data-model). U |
| `subtask.text` | `id`, `value`, `base_rev` | Text with revision. An empty value is `invalid` (FR-039). U |
| `subtask.done` | `id`, `done` (bool) | Fills in or clears `done_at`. U |
| `subtask.delete` | `id` | U |
| `week.notes` | `project_id`, `week`, `value` (HTML), `base_rev` | Text with revision in `week_notes`. Creates the row if it does not exist (FR-052) |

Every operation that references `project_id`, `task_id` or `id` requires the target to belong to the session's account. If it does not, the result is `not_found`.

## Static pages

| Path | Contents |
| --- | --- |
| `/` | app (`index.html`). Without a session, shows login or sign-up |
| `/password` | new password form. The token comes in the `#` fragment, which does not go to logs |
| `/terms`, `/privacy` | legal texts (R18) |
| `/sw.js` | service worker (R5) |
