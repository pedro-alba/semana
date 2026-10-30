---

description: "Implementation tasks for feature 005: prototype import and backup"
---

# Tasks: Prototype import and backup

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md)

**Tests**: required (constitution VI: all or nothing, isolation, conversion).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 [P] Create `tests/fixtures/prototype_v2.json`: v2 prototype state with `week` 3 weeks before 2026-10-26, two projects (`pessoal`, `trabalho`), tasks in different weeks (one open in the processed week, one done), a pending and a done subtask, `system` and `note` log entries, a due date, important, notes with `<strong>` and a `<script>`, `notes` for one week, a weekly event with `until` and one with no project, and a snapshot. Write the JSON by hand following `validateState` (lines 942–955 of `specs/semana.html`).
- [X] T002 [P] Create `tests/fixtures/prototype_v1.json`: v1 state with one task with a two-line text `description`, `urgency: "alta"`, `records` with a pending action (`next.state: "pendente"`), a done one and a report, and an http `links` entry (format read by `migrate`, lines 905–929).

---

## Phase 2: Foundational

- [X] T003 Create `src/semana/backup.py` with `router = APIRouter(prefix="/api")` and include it in `src/semana/app.py` like `accounts`, `reads` and `ops`.
- [X] T004 In `src/semana/backup.py`, pydantic models for the file per the [data-model](data-model.md), reusing from `semana.ops` `Monday`, `Html`, `Title`, `SubtaskText`, `ProjectName`, `Moment` and the rules of `EventSave` (inherit or reuse the model validator): `Backup(format: Literal["semana-backup"], version: Literal[1], processed_week: Monday, projects: list[Project] (min 1), tasks: list[Task], notes: list[Note], events: list[Event], snapshots: list[Snapshot])`; dates and times as `AwareDatetime`; a `model_validator` that checks unique IDs (projects, tasks, subtasks, log, events), that the `project_id` of tasks and notes is present in `projects`, and one notes block per project + week.

---

## Phase 3: User Story 2 - Keep a copy (Priority: P1)

Export comes before the prototype import because the app's format is the target of the conversion.

### Tests for User Story 2 ⚠️

- [X] T005 [P] [US2] Create `tests/api/test_backup_api.py::test_round_trip`: with `clock` and `new_account`, create via `/api/ops` tasks in two weeks (with subtasks, due date, important, progress, notes), week notes, a recurring event; move the clock forward one week to produce a snapshot; `GET /api/backup` has `format`, `version`, the data and the snapshot; change and delete things; `POST /api/backup` with the file returns `ok`; a new `GET /api/backup` equals the first one after replacing each ID with its position (function `without_ids` in the test) and ignoring `exported_at`.
- [X] T006 [P] [US2] In `tests/api/test_backup_api.py`, create `test_no_session` (GET and POST 401) and `test_empty_account` (exports only the two projects, and importing it back works).

### Implementation for User Story 2

- [X] T007 [US2] In `src/semana/backup.py`, `GET /api/backup`: `rollover.apply`; projects by `created_at`; tasks with subtasks and log (no `_rev` fields, no `account_id`) ordered by week, project and position; notes with `html <> ''`; events without `rev`; snapshots converted from `task_json` to the file's task format (drop the `_rev` fields); the account's `processed_week`; `exported_at` now.
- [X] T008 [US2] In `src/semana/backup.py`, `POST /api/backup` per [R2](research.md) and [R3](research.md): validate with `Backup` (error → 422 `{"error": "invalid", "fields": [...]}`, with the first element of each `loc`); inside `transaction(con)`: delete the account's projects, events and snapshots; insert with new IDs (old → new map), `position` rebuilt per project + week, HTML through `clean`, dates through `clock.iso`, revisions reset (`rev` 1 on events), an event with an unknown project gets no project, snapshots only for weeks before the current one and with tasks rewritten in the `task_json` format with the mapped IDs; `processed_week = min(file, monday(current) - 7)`. After the `COMMIT`, `rollover.apply`. Return `{"status": "ok"}`.

**Checkpoint**: T005–T006 pass.

---

## Phase 4: User Story 3 - An invalid file breaks nothing (Priority: P2)

### Tests for User Story 3 ⚠️

- [X] T009 [P] [US3] In `tests/api/test_backup_api.py`, create `test_invalid`: for each case (wrong format, `version` 2, no projects, task with an unknown `project_id`, title with 501 characters, repeated task IDs, week that is not a Monday), `POST` returns 422 and the following `GET /api/backup` equals the previous one.
- [X] T010 [P] [US3] In `tests/api/test_backup_api.py`, create `test_all_or_nothing`: with `monkeypatch` on `semana.backup.clean` to raise on the second call, the `POST` fails (500 or a `TestClient` exception with `raise_server_exceptions=False`) and the account stays the same.
- [X] T011 [P] [US3] In `tests/api/test_backup_api.py`, create `test_sanitize` (`<script>` and `onclick` in task and week notes do not reach the `GET`) and `test_rollover_after` (file with `processed_week` three weeks back and a task open in it: after the `POST`, the task is in the current week with a higher `weeks_open` and there is a snapshot of its week).
- [X] T012 [P] [US3] In `tests/api/test_isolation.py`, create `test_backup_isolated`: the file exported by A imported into B returns `ok`; A's `GET /api/backup` does not change; B's has A's content with IDs different from A's.

Implementation covered by T004 and T008.

---

## Phase 5: User Story 1 - Bring the prototype into the account (Priority: P1)

### Tests for User Story 1 ⚠️

- [X] T013 [P] [US1] Create `tests/e2e/test_backup_menu.py::test_conversion`: on `/terms`, import `/js/pure.js` and, via `page.evaluate`, `readBackup(text)` on `prototype_v2.json` and `prototype_v1.json` returns `format: "semana-backup"` with the fields from the [data-model](data-model.md) (v1: description in two paragraphs, `important`, pending and done actions as subtasks, report as a `note` log entry, link in the notes); on `{"x": 1}` and on text that is not JSON it returns `null`; an app file passes through as is.
- [X] T014 [P] [US1] In `tests/e2e/test_backup_menu.py`, create `test_import_prototype`: sign up, create a task "Old"; open the menu (now the profile menu, `open_menu`); `set_input_files` with `prototype_v2.json`; the confirmation shows the count of projects, tasks and events and the replace warning; Cancel: "Old" is still there; repeat and confirm: "Backup imported.", "Old" is gone, the file's tasks appear (open ones carried over to the current week) and the calendar shows the event.
- [X] T015 [P] [US1] In `tests/e2e/test_backup_menu.py`, create `test_export_and_invalid`: export with `page.expect_download`: name `semana-backup-` + date + `.json` and content with `format`; import some random JSON: "Invalid backup. Your current data was kept." with no confirmation; offline (`set_offline`), Export and Import show the connection warnings.

### Implementation for User Story 1

- [X] T016 [US1] In `src/semana/static/js/pure.js`, copy from the prototype with no logic change `assignOrder` (line 716), `migrate` (905), `normalize` (931) and `validateState` (942), and create:
  - `fromPrototype(s)`: v2 state → app file, per the table in the [data-model](data-model.md);
  - `readBackup(text)`: `JSON.parse` in a `try`; with `format === 'semana-backup'` it returns the object; otherwise `normalize(migrate(x))`, `validateState` and `fromPrototype`; any failure returns `null`;
  - `backupSummary(b)`: `{projects, tasks, events, weeks}` (distinct weeks across tasks and snapshots).
- [X] T017 [US1] In `src/semana/static/js/app.js`, put back in the header, before the profile, the prototype's Files menu (lines 1087–1088 of `specs/semana.html`) with only "Export full backup", "Import and replace" (a `<label>` with `<input id="import" type="file" accept=".json,application/json" hidden>`) and the backup text, in a `<div class="menu-pop" id="files-pop">`; a `files` variable ('' | the parsed backup object) controls the content, like `profile` in the profile menu, and goes back to '' when the menu closes. (Later moved into the profile menu: `backupHTML()` draws the BACKUP section inside `#profile-pop`, "Import and replace" is a button that clicks the hidden `#import`, and the `backupFile` variable, null or the parsed backup, controls the content.)
- [X] T018 [US1] In `src/semana/static/js/app.js`, export ([R4](research.md)): `flushEdits()`, `await data.send()`; if `await data.pending()` is still > 0 or the `GET /api/backup` fails on the network, `toast('No connection. Connect to export.')`; otherwise download the JSON (with `Blob` and `<a download>`, like the prototype's `download`) named `semana-backup-` + `today()` + `.json`.
- [X] T019 [US1] In `src/semana/static/js/app.js`, import: clicking "Import and replace" with no connection (`!navigator.onLine`) shows `toast('No connection. Connect to import.')` and does not open the file picker; on `change` of `#import`, a file > 50 MB or a null `readBackup` → `notice='Invalid backup. Your current data was kept.'` and `render()`; valid → `backupFile=b`, show in the menu (`#profile-pop`, originally `#files-pop`) the summary (`backupSummary`), "This deletes all of the account's current data and replaces it with the file's.", the pending changes (`t('backup.pending_discard', {n})` if `data.pending()` > 0) and the buttons "Import and replace" (`danger`) and "Cancel"; clear the input's `value`. Confirm: `POST /api/backup`; 422 → same invalid message; network → connection toast; ok → no `flushEdits` (the data is about to be replaced), `await data.clearAccount(account.id)`, `await enter()`, `notice='Backup imported.'`, `render()`.

**Checkpoint**: T013–T015 pass.

---

## Phase 6: Polish

- [X] T020 Run `uv run ruff check src tests` and `SEMANA_CHROMIUM=/usr/bin/chromium uv run pytest` (001–005); check the backup menu at 360 px and by keyboard; leave the [manual validation](quickstart.md) to the owner.

---

## Dependencies & Execution Order

- T001–T002 together; T003 → T004 → T007 → T008.
- US2 (T005–T008) before US1, because the app's format is the target of the conversion; US3 tests what T004 and T008 do.
- T016 → T017 → T018 → T019.

## Implementation Strategy

Server first (export and import of the app's format, with all the validation and isolation tests). Then the client: prototype conversion, menu, export and import.
