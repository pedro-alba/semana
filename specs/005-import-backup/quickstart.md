# Quickstart: Prototype import and backup

Running and prerequisites are the same as in [feature 001](../001-accounts-weekly-core/quickstart.md).

## Automated tests

```sh
SEMANA_CHROMIUM=/usr/bin/chromium uv run pytest
```

| Rule | The test proves |
| --- | --- |
| Round trip (SC-001) | export, change the account, import the file: exporting again gives the same content (except for IDs) |
| All or nothing (SC-003) | an invalid file and a failure in the middle of writing leave the account as it was |
| Isolation (SC-004) | importing A's file into B does not change A |
| Sanitizing (FR-024) | `<script>` and `onclick` in the file's notes do not reach the database |
| Rollover (FR-025) | file with an old processed week: open tasks move to the current week and closed weeks get a snapshot |
| Prototype (FR-020) | v1 and v2 prototype backups converted in the browser reach the account intact |
| Menu (FR-001, FR-022) | export downloads `semana-backup-YYYY-MM-DD.json`; import shows the summary, cancel changes nothing, confirm shows "Backup imported." |

## Manual validation

1. In the local prototype (`specs/semana.html`), use **Files → Export full backup**.
2. In the app, on a test account, open the profile menu and, under **BACKUP**, use **Import and replace** and pick that file. Check the summary and confirm.
3. Check old weeks (snapshots), formatted notes, subtasks, due dates and recurring events.
4. Use **BACKUP → Export full backup** in the app's profile menu, change a few tasks, import the exported file: the account goes back to what it was.
5. Try importing some other file (a `.json` from another program): "Invalid backup…" appears and nothing changes.
