---

description: "Implementation tasks for feature 002: calendar and due dates"
---

# Tasks: Calendar and due dates

**Input**: Design documents from `/specs/002-calendar-due-dates/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md)

**Tests**: required where the rule is subtle (constitution VI): recurrence, overlap, event conflict, validation, isolation and offline use.

**Organization**: by spec story. Feature 001 is implemented. References to lines of `specs/semana.html` point to the original prototype, from which the calendar code was removed in 001.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

Nothing to prepare: project, dependencies and tools come from feature 001.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: the migration and the pure functions come before any story.

- [X] T001 Create `src/semana/migrations/002_calendar.sql`, the next `user_version`, per [data-model.md](data-model.md) (now part of `migrations/001_initial.sql`):
  - **task**: `ALTER TABLE task ADD COLUMN due TEXT` (ISO date or NULL).
  - **event**: `CREATE TABLE event` with these exact columns and constraints:
    - `id TEXT PRIMARY KEY`;
    - `account_id TEXT NOT NULL REFERENCES account(id) ON DELETE CASCADE`;
    - `project_id TEXT REFERENCES project(id) ON DELETE CASCADE`;
    - `title TEXT NOT NULL`;
    - `start TEXT NOT NULL` and `end TEXT NOT NULL`;
    - `all_day INTEGER NOT NULL DEFAULT 0 CHECK (all_day IN (0,1))`;
    - `repeat TEXT NOT NULL DEFAULT 'none' CHECK (repeat IN ('none','weekly','monthly'))`;
    - `until TEXT`;
    - `location TEXT NOT NULL DEFAULT ''` and `description TEXT NOT NULL DEFAULT ''`;
    - `rev INTEGER NOT NULL DEFAULT 1`;
    - `created_at TEXT NOT NULL` and `updated_at TEXT NOT NULL`.
  - **Index**: `CREATE INDEX event_start ON event(account_id, start)`.
- [X] T002 [P] In `src/semana/static/js/pure.js`, recover from the prototype and export, without changing the logic:
  - `occurrences(e, ws)` (lines 745–755);
  - `layoutEvents(list)` (lines 756–762);
  - `weekday`, `monthShort` and `fmtDay` (lines 706–708).

**Checkpoint**: `uv run pytest` still passes, with the migration applied over a 001 database.

---

## Phase 3: User Story 1 - Give a task a due date (Priority: P1) 🎯 MVP

**Goal**: optional due date per task, shown in the document and on the card and kept by the rollover.

**Independent Test**: due dates of today, tomorrow, another day this week, a future date and a past one; finish a task; simulate the rollover; check the texts and that the date is kept.

### Tests for User Story 1 ⚠️

- [X] T003 [P] [US1] In `tests/api/test_ops.py`, add the `task.due` tests:
  - setting `"2026-11-06"` shows in `GET /api/week` as `due`;
  - `null` removes the due date;
  - `"2026-13-01"` and `"tomorrow"` give `invalid`;
  - the operation changes `updated_at` (FR-005);
  - resending the same operation changes nothing.
- [X] T004 [P] [US1] In `tests/api/test_rollover.py`, add `test_due_kept`: an open task with a due date, carried over by the rollover, keeps the due date, and the closed week's snapshot contains `"due"` (FR-002, FR-007).
- [X] T005 [P] [US1] In `tests/api/test_isolation.py`, add to `CASES` the `task.due` operation with the `id` of one of A's tasks.

### Implementation for User Story 1

- [X] T006 [US1] In `src/semana/ops.py`, create `@operation("task.due", TaskDue)`:
  - Fields: `id` and `value: date | None`. The date is validated as a real ISO date.
  - Writes `due = value.isoformat()` or NULL and calls `touch_task`.
  - If the task is not the account's, `not_found`.

  In `src/semana/reads.py`, add `"due": t["due"]` to `task_json`. With that, `GET /api/week` and the rollover snapshot get the field.
- [X] T007 [US1] In `src/semana/static/js/app.js`, wire the due date to the client:
  - **Adapters**: `fromAPI` gains `due: x.due || ''` and `toAPI` gains `due: t.due || null`.
  - **`isBlank`**: add `&& !t.due` (FR-006).
  - **Prototype functions** (lines 1116–1126 and 1225): recover `dueState(t)` and `dueShort(t)`, which depend on `today()`, and `setDue(t, v)`, with its body replaced by:

    ```
    v=validDate(v)?v:'';if(v===t.due)return;t.due=v;touch(t);persist();
    data.enqueue({op:'task.due',id:t.id,value:v||null});refreshMeta(t);drawList()
    ```

    To compute "today", `today()` must use `Date.now() + offset` in the account's time zone, like 001's `tick`.
  - **Card** (`cardSubHTML`): put back the prototype snippet that inserts `<span class="card-due…">` after "↪ week N". Finished tasks do not show the due date (FR-003).
  - **Document** (`metaHTML`): put back the "Due date" button, with `<input type="date">` and `data-act="due-pick"`, and the × that removes it, after project, week and weeks open (FR-004). In `readOnly()`, the due date is only shown (FR-001).
  - **`due-pick` handler**: calls `setDue`.

**Checkpoint**: T003–T005 pass and the US1 independent test works by hand.

---

## Phase 4: User Story 2 - See and add events in the week (Priority: P1)

**Goal**: the Calendar screen with one-off, all-day and recurring events.

**Independent Test**: create a one-off event, a multi-day all-day event, a weekly event with an end date and a monthly event on the 31st; browse 24 months; edit and delete the series.

### Tests for User Story 2 ⚠️

- [X] T008 [P] [US2] Create `tests/e2e/test_recurrence.py`, loading `pure.js` as in `tests/e2e/test_pure.py` (SC-003). For each week from `2026-01-05` to `2027-12-27`, compare `P.occurrences(e, ws)` with the expected list, computed in Python inside the test:
  - weekly on Tuesdays 09:00–10:00 with `until` `2026-03-31`: the last occurrence is 03/31 (inclusive) and there is none after it;
  - monthly on the 31st: no occurrence in February, April, June, September and November;
  - monthly on the 29th: February only in 2028, so no February occurrence inside the window;
  - weekly crossing `2026-12-28 → 2027-01-04`;
  - one-off from 23:00 to 01:00 the next day, which shows on both days;
  - 3-day all-day event (exclusive `end`).

  Also `P.layoutEvents` with three overlapping `{a, b}` items: three distinct `lane` values and `columns` 3.
- [X] T009 [P] [US2] In `tests/api/test_ops.py`, add the event tests:
  - **Create**: `event.save` with `base_rev` 0 creates and responds `ok` with `rev` 1.
  - **Resend**: the same payload with `base_rev` 0 responds `ok` with `rev` 1, without duplicating.
  - **Update**: with `base_rev` 1, responds `rev` 2.
  - **Conflict**: another client with `base_rev` 1 and different values gets `conflict`, with `value` equal to the current event and `rev` 2.
  - **Deleted**: `event.delete` followed by `event.save` with `base_rev` 2 gives `conflict` with `value` `null`. The resend with `base_rev` 0 recreates the event.
  - **Validation** (all `invalid`):
    - `end <= start`;
    - 32-day duration;
    - `repeat` `weekly` without `until`;
    - `until` with `repeat` `none`;
    - `until` before the date of `start`;
    - `repeat` `daily`;
    - empty title or one with 161 characters;
    - location with 501 characters;
    - description with 10,001 characters.
  - **Project**: a nonexistent `project_id` gives `not_found`.
  - **Delete again**: repeating `event.delete` gives `ok`.
- [X] T010 [P] [US2] Create `tests/api/test_agenda.py`, with the `clock` fixture and current week `2026-10-26`:
  - **Candidate series** (R2) in `GET /api/agenda?week=2026-10-26`:
    - shown: a one-off this week, a one-off from the previous week that ends in this one, and a weekly series started in August with `until` in December;
    - not shown: a one-off in September, a series with `until` on `2026-09-01` and an event that starts on `2026-11-02`.
  - **Invalid week**: 422 if the week is not a Monday.
  - **Account deletion**: after `DELETE /api/account`, the `event` table has no rows for the account.

### Implementation for User Story 2

- [X] T011 [US2] In `src/semana/ops.py`, create the `EventSave` model and the operations.
  - **Model fields**: `id`, `project_id: str | None`, `title`, `start`, `end`, `all_day: bool`, `repeat`, `until: str | None`, `location`, `description` and `base_rev: int`.
  - **Exact constraints** (R6):
    - `title` with 1–160 characters, trimmed;
    - `start` and `end` in the `YYYY-MM-DDTHH:MM` format and valid dates;
    - `end > start` and `end <= start + 31 days`;
    - `repeat` in `none`, `weekly` or `monthly`;
    - `until` (ISO date) required if `repeat <> 'none'` and `None` otherwise, with `until >= start[:10]`;
    - `location` up to 500 characters and `description` up to 10,000.
  - **`@operation("event.save")`**:
    - `project_id` given and outside the account: `not_found`.
    - Row does not exist:
      - `base_rev == 0`: inserts with `rev` 1 and responds `ok`, `rev` 1;
      - otherwise: `conflict` with `value` `None` and `rev` 0.
    - Row from another account: `not_found`.
    - Row from the account with every field equal: `ok` with the current `rev`.
    - `base_rev == rev`: updates the fields and `updated_at`, increments `rev` and responds `ok`.
    - In all other cases: `conflict` with `value` equal to `event_json(row)` and the current `rev` (R3).
  - **`@operation("event.delete", IdOnly)`**: `DELETE … WHERE id = ? AND account_id = ?`, always `ok`.
- [X] T012 [US2] In `src/semana/reads.py`, create `GET /api/agenda?week=`:
  - Runs `rollover.apply` and responds 422 if the week is not a Monday.
  - `event_json(row)` builds the contract fields, with `all_day` as a bool.
  - **`events`**: candidate series with `account_id = ? AND start < :s7 AND (end > :s OR (repeat <> 'none' AND until >= :s_minus_31))`, where `s7 = add_days(s, 7) + 'T00:00'`, `s` as the local datetime `s + 'T00:00'` and `s_minus_31` as a date.
  - **`dues`**: returns `[]` for now; T017 fills it in.
- [X] T013 [P] [US2] In `src/semana/static/js/data.js`:
  - **Read**: `agenda(monday)` like `week()`, with the cache key `agenda|<monday>`. With no network and no cache, throws `{kind: 'offline'}`.
  - **Coalescing**: `event.save` joins the coalescing of pending ops by the `id` target, like the text operations, replacing the whole payload except `base_rev`.
  - **Revision**: the `base_rev` adjustment after an `ok` with `rev` applies to it too.
- [X] T014 [US2] In `src/semana/static/js/app.js`, recover the Calendar screen from the prototype:
  - **Functions**: `openEvent` (line 1582), `eventEditor` (1590), `drawCalendar` (1607), `eventValues` (1624) and `syncEventFrequency` (1628). The `screen` variable now accepts `'calendar'`, and `filter` is the project filter.
  - **Header** (`headerHTML`): the `calendar` "Calendar" button comes back (FR-010).
  - **Recovered handlers**: `calendar`, `tasks`, `new-event`, `slot`, `event`, `close-event`, `ask-delete-event`, `cancel-delete`, `delete-event`, `open-location` and the `submit` of `#event-form`, plus Esc closing the editor.
  - **`S.events`**: comes from `data.agenda(week)` through the event adapter in [data-model.md](data-model.md#client). The agenda is loaded when the Calendar opens and on every week change there, and on each `persist()` it goes back into the cache with the reverse adapter.
  - **Save** (`submit`):
    - validate on the client the same rules as T011, with a message in the form's `.error` (FR-022);
    - new `id`: `crypto.randomUUID()`;
    - update `S.events`;
    - enqueue `event.save` with `base_rev: e.rev || 0`;
    - **before converting, the all-day "last day" becomes an exclusive `end`**, as in `eventValues`.
  - **Delete**: `delete-event` enqueues `event.delete`.
  - **Series warning**: keep the prototype's warning for series with no end date.
  - **`data.onRev`**: updates `e.rev`.
  - **`events()`**: `S.events.flatMap(e => occurrences(e, week))`, without the due-date part, which is left for US3.
  - **"Location or link"**: the button uses `parseLink` and `openLink`/`copyPath` from 001 (FR-026).
  - **Offline**: opening the calendar on a week with no cache shows the connection notice from 001 (FR-041).

**Checkpoint**: T008–T010 pass and the US2 independent test works by hand.

---

## Phase 5: User Story 3 - Due dates in the calendar and "On the agenda" (Priority: P2)

**Goal**: due-dates band in the calendar and the "On the agenda" section in the overview.

**Independent Test**: due dates and events in several projects and one due date that passed last week; check the calendar and the overview of the current week.

### Tests for User Story 3 ⚠️

- [X] T015 [P] [US3] In `tests/api/test_agenda.py`, add the `dues` tests:
  - **Current week `2026-10-26`**, with due dates:
    - on 10/28 on an open task in Personal;
    - on 10/30 on a finished task in Work;
    - on 10/15 on an open task (overdue);
    - on 10/15 on a finished task;
    - on 11/05.
  - **Result in the current week**: 10/28, 10/30 and the open overdue one show. The finished one from 10/15 and 11/05 do not. Each item carries `week` with the week the task is in.
  - **Week `2026-10-19`**, which is not the current one: the open 10/15 item shows because it is in the week, and no overdue item is added.
- [X] T016 [P] [US3] In `tests/api/test_isolation.py`:
  - add to `CASES` the operations `event.save` (with A's `project_id` and, separately, with the `id` of one of A's events) and `event.delete` (with A's `id`);
  - create `test_agenda_isolated`: B sees none of A's events or due dates in `GET /api/agenda`.

### Implementation for User Story 3

- [X] T017 [US3] In `src/semana/reads.py`, fill in `dues` in `GET /api/agenda` per [contracts/api.md](contracts/api.md):
  - `SELECT id AS task_id, project_id, week, title, due, progress, important FROM task WHERE account_id = ? AND due >= :s AND due < :s7`;
  - in the current week, `UNION` with `… AND progress < 100 AND due < :s`;
  - `important` as a bool.
- [X] T018 [US3] In `src/semana/static/js/app.js`, recover the due-dates band and the agenda from the prototype:
  - **`dueEventHTML(t)`** (line 1603) and the "Due dates" band of `drawCalendar`: now use `S.dues`, the agenda's `dues` list adapted to `{id: task_id, projectId: project_id, week, title, due, progress, important}`, filtered by `filter`. The order is: open first, important first, then title (FR-030).
  - **Opening a due date** (`open-task`): switches to the task's week and project (`week`, `project`), loads with `load` and opens the task (FR-031). Works both in the calendar and in the agenda.
  - **"On the agenda" section** in `dashboardHTML`: recover from the prototype (lines 1166–1186 of the original) the snippet that builds the items and the `p-agenda` panel, with the `calendar` link "View week ↗" and up to 9 items (FR-032):
    - overdue items come from `S.dues` with `due < week`, only in the current week;
    - due dates of the week's open tasks;
    - occurrences from `events()`;
    - events trigger `event` and open the calendar on the week with the editor (FR-033).
  - **Loading**: the overview also calls `data.agenda(week)` when loading the week, for "On the agenda".
  - **Local update**: when a task's due date changes (T007), update or remove the matching item in `S.dues` and rewrite the `agenda|<week>` cache.

**Checkpoint**: T015 and T016 pass and the US3 independent test works by hand.

---

## Phase 6: User Story 4 - Calendar offline and across devices (Priority: P2)

**Goal**: the 001 guarantees apply to events and due dates.

**Independent Test**: offline, create an event and change a due date, reopen the tab, reconnect and check in another context; conflict in two windows.

### Tests for User Story 4 ⚠️

- [X] T019 [P] [US4] In `tests/e2e/test_offline.py`, create two tests:
  - **`test_calendar_offline`** (SC-006):
    1. Open the Calendar and a task.
    2. `set_offline(True)`.
    3. Create an event at 14:00 and set the task's due date.
    4. Close and reopen the page, still offline: both show.
    5. Reconnect until the footer shows "Saved".
    6. In a second context, check both.
  - **`test_event_conflict`**:
    1. Two contexts open the editor of the same event.
    2. The first changes the title and saves.
    3. The second changes the title and saves, and sees the warning with both versions.
    4. "Keep my version" makes the first context, after reloading, show the second one's title.

### Implementation for User Story 4

- [X] T020 [US4] In `src/semana/static/js/app.js`, extend 001's `data.onConflict` handling to `op.op === 'event.save'` (FR-042):
  - **Warning in the event editor** (`eventEditor`, no modal): "This event was changed on another device after you opened it.", or "…was deleted on another device." when `value` is `null`.
  - **"Keep my version"**: sets `e.rev = rev`, or 0 if it was deleted, and enqueues the local payload again.
  - **"Use the other version"**: replaces the event in `S.events` with the adapted `value`. If `value` is `null`, removes the event and closes the editor.
  - **Discarded version**: title, when and location, as text, in a block with "Copy" until the ×.
  - **Editor closed**: a toast "Conflict in “<title>”." with "View" opens the calendar on the event's week, with the editor open.

**Checkpoint**: T019 passes.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T021 [P] In `tests/e2e/test_keyboard_mobile.py`, add `test_calendar_keyboard_mobile` (SC-007), at 360×740 with `has_touch`, keyboard only:
  1. Open Calendar.
  2. "+ New event".
  3. Fill in title, start and end.
  4. Save.
  5. Esc.
  6. Open a task and set the due date through the date field.

  Also assert that `scrollWidth <= 360`.
- [X] T022 Run `uv run ruff check src tests` and `uv run pytest` (all 001 and 002 tests) and go through the manual validation in [quickstart.md](quickstart.md), fixing any differences.

---

## Dependencies & Execution Order

- **Foundational (T001–T002)**: blocks every story.
- **US1 (due date)** and **US2 (events)**: independent of each other after the base. They can run in parallel, but T007 and T014 touch the same `app.js`.
- **US3**: depends on US1 (due dates) and US2 (calendar and agenda).
- **US4**: depends on US2. The offline due-date test also needs US1.
- **Polish**: after all of them.

```text
T001,T002 → US1 ─┐
          → US2 ─┼→ US3
                 └→ US4 → Polish
```

### Parallel Opportunities

- T002 in parallel with T001.
- **US1**: T003, T004 and T005 together.
- **US2**: T008, T009 and T010 together. T013, which is in `data.js`, runs in parallel with T011 and T012.
- **US3**: T015 and T016 together.
- T021 in parallel with US4.

## Parallel Example: User Story 2

```bash
Task: "T008 tests/e2e/test_recurrence.py"
Task: "T009 event in tests/api/test_ops.py"
Task: "T010 tests/api/test_agenda.py"
Task: "T013 agenda() and coalescing in src/semana/static/js/data.js"
```

## Implementation Strategy

1. **MVP**: base and US1. The due date already delivers value on its own, without the Calendar screen.
2. US2: the full Calendar.
3. US3: brings due dates and events together in the agenda and the overview.
4. US4: the outage and conflict test. The mechanism comes from 001; here only the warning in the editor is added.
5. Polish: keyboard, 360 px and full validation.

## Notes

- Every new operation needs a case in `tests/api/test_isolation.py`, or the isolation test fails.
- The prototype is still the reference. When recovering a function from it, change only what the API and the queue need.
