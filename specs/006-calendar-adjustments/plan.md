# Implementation Plan: Calendar adjustments, project memory and event search

**Branch**: `006-calendar-adjustments` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

## Summary

It is mostly a client change, with two small server adjustments:

- **Server**: the migration `004_repeat.sql` rebuilds `event` with `repeat IN ('none','daily','weekly','monthly')` (the migrations were later folded into a single `001_initial.sql`). `event.save` now accepts `daily` and an optional `until`. `/api/agenda` now returns series with no end date. `/api/search` now returns events.
- **Client**: the editor changes order. `occurrences` gains `daily`. Events get a details card and dragging with Pointer Events. The project and the visibility are remembered in `localStorage`. Search now includes events.

## Technical Context

**Language/Version**: Python 3.12; JavaScript ES2022 with no build

**Primary Dependencies**: none new. Dragging uses native Pointer Events, no library

**Storage**: SQLite, with migration 004, which rebuilds the table, because in SQLite a `CHECK` cannot be altered. In the browser, the keys `semana-project|<account>` and `semana-visibility|<account>`

**Testing**: pytest (`daily`, null `until`, agenda with an endless series, search) and pytest-playwright (editor, dragging, card, memory, search)

**Constraints**: whole series when dragging; conflict through the event's revision (002); offline through the queue

## Constitution Check

| Principle | How it complies | Status |
| --- | --- | --- |
| I. Fewer controls | "Repeat until" only shows when it makes sense. Details show on hover, without opening the editor | ✅ |
| III. Nothing is lost | Dragging saves through the queue, with revision and conflict warning. Dropping outside the grid does not save | ✅ |
| IV. Isolated accounts | Search filters by `account_id`. The project memory is separate per account | ✅ |
| V. Simplicity | No dependency. The migration is SQLite's standard table rebuild | ✅ |
| VI. Tests | Daily and endless recurrence, dragging a series, search | ✅ |

## Decisions (research)

- **R1. Dragging**:
  - `pointerdown` on a `.cal-event` or an `.all-day-event` with `pointerType !== 'touch'`. Up to 4 px of movement counts as a click.
  - While dragging, only the block moves (`transform`). The column and the minute come from `elementsFromPoint` on the `.cal-day` and from `clientY` relative to the grid (1 px = 1 min), rounded to 15.
  - On drop: delta = new start − occurrence start. It is applied to the series' `start` and `end`. `until` shifts by the delta's days when it would fall before the new start. Then `submitEvent` with the values (the same path as the editor).
- **R2. Details card**:
  - A single `#event-card` (`role="tooltip"`), positioned with `getBoundingClientRect` and kept inside the window.
  - It shows on `pointerover` (mouse), after 300 ms, and on `focusin`. It hides on `pointerout`, `focusout`, when a drag starts and on redraw.
  - The button gets `aria-describedby`.
- **R3. Next occurrence**: pure function `nextOccurrence(e, today)`. It searches week by week from today's week, up to one year. If the series ended, it returns the last week with an occurrence; if it is a one-off, the start's week. It uses the same `occurrences` as the calendar.
- **R4. Memory**: written in `goTo()`, when the project changes, and on the visibility's `change`. Read in `enter()`, checking that the project still exists.

## Project Structure

```text
src/semana/migrations/004_repeat.sql     # new (later folded into 001_initial.sql)
src/semana/ops.py                        # daily; optional until
src/semana/reads.py                      # agenda with null until; events in search
src/semana/static/js/pure.js             # occurrences daily; searchItems with events; nextOccurrence
src/semana/static/js/app.js              # editor, card, dragging, memory, search
src/semana/static/app.css                # card and dragging
tests/api/test_ops.py, test_agenda.py, test_search_index.py, test_isolation.py
tests/e2e/test_recurrence.py             # daily, endless, nextOccurrence
tests/e2e/test_calendar_006.py           # new: editor, card, dragging, memory, search
```

## Complexity Tracking

No additions.
