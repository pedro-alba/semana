---

description: "Tasks for feature 006: calendar adjustments, project memory and event search"
---

# Tasks: Calendar adjustments, project memory and event search

**Input**: [plan.md](plan.md), [spec.md](spec.md), [contracts/api.md](contracts/api.md)

## Phase 1: Foundational (server and pure functions)

- [X] T001 Create `src/semana/migrations/004_repeat.sql`: `CREATE TABLE event_new` equal to `event` (002) with `CHECK (repeat IN ('none','daily','weekly','monthly'))`; `INSERT INTO event_new SELECT * FROM event`; `DROP TABLE event`; `ALTER TABLE event_new RENAME TO event`; recreate `event_start`. (Later folded into `001_initial.sql`.)
- [X] T002 In `src/semana/ops.py` (`EventSave`): `repeat` accepts `"daily"`; the rule becomes "`none` requires a null `until`" (no longer requiring `until` for the others).
- [X] T003 In `src/semana/reads.py`: in the agenda, `(repeat <> 'none' AND (until IS NULL OR until >= ?))`; in search, `events` with the fields from [contracts/api.md](contracts/api.md).
- [X] T004 [P] API tests: in `tests/api/test_ops.py`, `daily` without `until` is `ok`, `none` with `until` is `invalid`; in `tests/api/test_agenda.py`, a weekly series with no `until` started a year earlier shows in the agenda; in `tests/api/test_search_index.py`, the index includes the event; in `tests/api/test_isolation.py`, B's search does not return A's events (`test_search_isolated` already compares the whole index: adjust the expected value to include `"events": []`).
- [X] T005 In `src/semana/static/js/pure.js`: `occurrences` with `repeat==='daily'` (every date ≥ start); `nextOccurrence(e, today)` (R3) returning the occurrence date; `searchItems(tasks, notes, events=[])` with items `{kind:'event', id, e, title, body: location + description, week, projectId, at:''}`, where `week` is the week of `nextOccurrence`. In `rankSearch`, nothing changes (events come in through title and body; recents still have only tasks).
- [X] T006 [P] In `tests/e2e/test_recurrence.py`: `daily` produces 7 occurrences in a week after the start and none before; a weekly series with no `until` shows 3 years later; `nextOccurrence` for a one-off, a running weekly series, an ended series and a future series.

## Phase 2: US1 Editor

- [X] T007 In `src/semana/static/js/app.js`: `FREQUENCIES` with `daily`; `eventEditor` in the order of FR-001, with `<select name="repeat">` ("Once", "Every day", "Every week", "Every month, same day") and `#event-until` (label "Repeat until · optional") hidden when `repeat==='none'`; `eventValues` reads `repeat` from the select and discards `until` with "Once"; `syncEventFrequency` shows or hides `#event-until` on the select's `change`; remove the warning about a series with no end date.
- [X] T008 In `src/semana/static/js/app.js`, FR-002: store the duration on `focus`/`input` (`form.dataset.dur` in minutes or days) and, on `change` of `start`, if `end <= start`, `end = start + dur` (for all day, in days).
- [X] T009 [P] In `tests/e2e/test_calendar_006.py::test_editor`: field order; "Repeat until" hidden with "Once" and visible with "Every day"; moving the start after the end moves the end with the same duration; save "Every day" with no date and check 7 blocks next week.

## Phase 3: US2 Card and dragging

- [X] T010 In `src/semana/static/js/app.js` and `app.css`, details card (R2): `eventCardHTML(e)` with title, day and time (`fmtDay`, `start.slice(11,16)`–`end.slice(11,16)` or "All day"), frequency (e.g. "Every Monday, until 12/31"; no suffix when there is no end date), project, location and up to 160 characters of the description; show on `pointerover` (only `pointerType==='mouse'`, 300 ms) and `focusin` on `.cal-event`/`.all-day-event`, hide on `pointerout`/`focusout`, when dragging and in `drawCalendar`.
- [X] T011 In `src/semana/static/js/app.js` and `app.css`, dragging (R1): `data-occ` with the occurrence start on the blocks; non-touch `pointerdown` on a block stores the origin; `pointermove` beyond 4 px enters drag mode (class `dragging`, `setPointerCapture`), computes the day and minute under the pointer and shifts the block with `transform`; `pointerup` in drag mode computes the delta, applies it to the series (`start`, `end`, `until` if needed) and saves through the same path as `saveEvent` (refactor the end of `saveEvent` into `submitEvent(ev)`); outside the grid, it only redraws. The `click` that follows a drag is ignored.
- [X] T012 [P] In `tests/e2e/test_calendar_006.py`: `test_card` (hovering shows title, time, location; leaving hides it; keyboard focus shows it); `test_drag` (dragging a one-off from Tuesday 09:00 to Wednesday 11:00 stores shifted `start` and `end`; dragging an occurrence of a weekly series changes the series in the database; a click without dragging opens the editor).

## Phase 4: US3 Project memory

- [X] T013 In `src/semana/static/js/app.js` (R4): `remember(key, value)` and `remembered(key)` with `localStorage` (try/catch) at `semana-project|<account.id>` and `semana-visibility|<account.id>`; write in `goTo()` and on `change` of `#project` in the calendar; in `enter()`, use the remembered values if the project exists.
- [X] T014 [P] In `tests/e2e/test_calendar_006.py::test_memory`: pick Work in Tasks and Personal in the Calendar, reload: Tasks opens on Work and the Calendar on Personal; another account in the same browser opens on the first project.

## Phase 5: US4 Event search

- [X] T015 In `src/semana/static/js/app.js`: `currentSearchItems` passes the index's events (overridden by `S.events` by id) converted with `eventFromAPI`; `drawResults` with a calendar icon and the meta "Event · project · occurrence date"; placeholder "Search tasks, notes and events"; `chooseResult` for `event`: `screen='calendar'`, `filter=''` if the filter hides the event (and remember it), `await go(week)`, scroll to the occurrence's block, focus it (the card shows through focus).
- [X] T016 [P] In `tests/e2e/test_calendar_006.py::test_search`: create a weekly "English class" with location "School" starting two weeks ago; search "school": the result has the calendar icon; Enter goes to the Calendar on the current week with the block focused and the card visible.

## Phase 6: Polish

- [X] T017 `uv run ruff check src tests` and `SEMANA_CHROMIUM=/usr/bin/chromium uv run pytest`; screenshots of the editor and the card for review.
