---

description: "Tasks for feature 007: single occurrences, duration by dragging and agenda summary"
---

# Tasks: Single occurrences, duration by dragging and agenda summary

**Input**: [plan.md](plan.md), [spec.md](spec.md)

## Phase 1: Foundational

- [X] T001 Create `src/semana/migrations/005_event_extra.sql`: `ALTER TABLE event ADD COLUMN fills_day INTEGER NOT NULL DEFAULT 0 CHECK (fills_day IN (0,1))` and `ALTER TABLE event ADD COLUMN skipped TEXT NOT NULL DEFAULT '[]'`. (Later folded into `001_initial.sql`.)
- [X] T002 In `src/semana/ops.py`, `EventSave` gains `fills_day: bool = False` and `skipped: list[date] = Field(default_factory=list, max_length=1000)`; `row()` writes `int(fills_day)` and `json.dumps` of the dates sorted and deduplicated; `EVENT_FIELDS` includes both. In `src/semana/reads.py`, `event_json` returns `fills_day` (bool) and `skipped` (list).
- [X] T003 [P] API tests: in `tests/api/test_ops.py`, save with `skipped` and `fills_day` and read through the agenda; more than 1,000 dates is `invalid`; in `tests/api/test_backup_api.py`, the round trip keeps both fields.
- [X] T004 In `src/semana/static/js/pure.js`: `occurrences` skips `e.except` (list of dates); `repeatText(e)` ("Every day", "Every Tuesday", "Every month on the 15th", with ", until 12/15"); in `src/semana/static/js/app.js`, `eventFromAPI`/`eventToAPI` map `fills_day↔fullDay` and `skipped↔except`.
- [X] T005 [P] In `tests/e2e/test_recurrence.py`: skipped dates disappear from the occurrences and from the next occurrence; `repeatText` for the four cases.

## Phase 2: US1 and US2 (series and edge)

- [X] T006 In `src/semana/static/js/app.js`: blocks with `<span class="resize">` on the day they end; dragging gains `mode: 'move' | 'resize'`; on the edge, only `end` changes (15-minute steps, minimum 15).
- [X] T007 In `src/semana/static/js/app.js`: when dropping a recurring event, `askSeries(block, {one, series})` shows `#series-pop` next to the block ("Change only this one or the whole series?"); "Only this one" → series with `except` + the occurrence date and a new standalone event (new `id`, `repeat:'none'`, `until:''`, `except:[]`, new time); "Whole series" → as in 006; Cancel, Esc or a click outside → `drawCalendar()`.
- [X] T008 In `src/semana/static/js/app.js`: `openEvent(id, …, occ)` stores `draft.occurrence` (from the block's or summary row's `data-occ`); deleting a recurring event with a known occurrence offers "Only this one" (series with the date in `except`) and "Whole series".
- [X] T009 [P] In `tests/e2e/test_calendar_007.py`: `test_only_this_one_when_dragging`, `test_cancel`, `test_edge` (resizing a one-off and a series, with "Whole series"), `test_delete_only_this_one`.

## Phase 3: US3 and US4

- [X] T010 In `src/semana/static/js/app.js`: in the editor, `<label id="event-full">` "Fill the whole day", visible only with "All day"; in `drawCalendar`, an all-day event with `fullDay` becomes a 00:00–24:00 block in the grid (day-only dragging); the "All day" strip is only drawn if it has something.
- [X] T011 In `dashboardHTML` (`src/semana/static/js/app.js`): group occurrences by `id` and keep one (current week: the first with `end` > now, otherwise the last; other weeks: the first); the "recurring" text becomes `repeatText(e)`; the details card also uses `repeatText`; summary rows carry `data-occ`.
- [X] T012 [P] In `tests/e2e/test_calendar_007.py`: `test_all_day` (the strip goes away when empty; checked goes to the grid); `test_summary_and_card` (daily shows once with "Every day, until …").

## Phase 4: US5

- [X] T013 In `src/semana/static/app.css`, Graphite: increase the card gradient mix (dark: 24%→32% and 10%→17%, the most that keeps 4.5:1 contrast on a task at 0%; light: 34%→46% and 14%→24%); in `cardSubHTML`, remove "No subtasks".
- [X] T014 In `tests/e2e/test_appearance_panel.py::test_contrast`, blend the strongest layer in Graphite (the progress color at the left percentage over `--surface`) before measuring; remove the `ponytail` comment that pointed at that limit.

## Phase 5: Polish

- [X] T015 `uv run ruff check src tests`, the full suite twice, and screenshots of the bubble, the edge and the summary.
