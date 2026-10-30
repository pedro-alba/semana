# API contract: Import and backup

Conventions from the [001 contract](../../001-accounts-weekly-core/contracts/api.md).

## `GET /api/backup`

Returns the backup file of the session's account ([data-model](../data-model.md)). Before building it, applies the rollover. No session: 401.

## `POST /api/backup`

Body: the app backup file.

| Response | When |
| --- | --- |
| `200 {"status": "ok"}` | The account's data was replaced by the file's, in one transaction, and the rollover ran |
| `422 {"error": "invalid", "fields": [...]}` | The file failed validation. Nothing changed |
| `401` | No session |

- **Scope:** writes only to the session's account. All IDs are generated again.
- **What stays:** appearance, e-mail, password and sessions do not change.
