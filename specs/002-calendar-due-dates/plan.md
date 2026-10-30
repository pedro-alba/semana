# Implementation Plan: Calendar and due dates

**Branch**: `002-calendar-due-dates` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-calendar-due-dates/spec.md`

## Summary

Bring back to the app the parts of the prototype that feature 001 removed: due dates on tasks, the Calendar screen with recurring events, and "On the agenda" in the overview.

- **Server**: gains the `task.due` column, the `event` table (one row per series, with a revision for conflicts), three new operations and the `GET /api/agenda` route.
- **Client**: recovers the calendar, due date and agenda functions from the prototype and wires them to the operation queue from 001. Occurrences are still computed in the browser, as in the prototype.

## Technical Context

**Language/Version**: Python 3.12 (server); JavaScript ES2022 with no build (client), same as 001

**Primary Dependencies**: none new (FastAPI, uvicorn, nh3)

**Storage**: SQLite. Migration `002_calendar.sql`, with one new column and one new table (now part of `migrations/001_initial.sql`)

**Testing**: pytest + pytest-playwright, as in 001. Recurrence is tested in the browser with `page.evaluate`

**Target Platform**: local, for now (deploy postponed since 001)

**Project Type**: web application (same process as 001)

**Performance Goals**: calendar usable in ≤ 1 s with 50 events and 30 due dates (SC-004)

**Constraints**: no modal, offline editing, conflicts never silent, 360 px and keyboard

**Scale/Scope**: 1 table, 1 column, 3 operations, 1 route and about 300 lines of client code recovered from the prototype

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How the plan complies | Status |
| --- | --- | --- |
| I. Fewer controls, more text | Reproduces the prototype's interface (Calendar navigation, side editor, due-dates band, "On the agenda"). Reminders, invitations, integrations and dragging on the grid stay out | ✅ |
| II. The week is the unit | The due date does not move the task to another week. The rollover keeps the due date and the snapshot records it. The grid is weekly | ✅ |
| III. Nothing gets lost | The new operations go through the 001 queue. An event conflict warns and lets the person choose, including when the event was deleted on another device (R3). Deleting asks for confirmation | ✅ |
| IV. Each account's data is its own | `account_id` in the new table and in every query. The event's `project_id` is checked. There are isolation cases for every new operation and for `/api/agenda`. Event texts are shown through `esc` | ✅ |
| V. Simplicity | No new dependency or layer. Recurrence expansion reuses the prototype's code instead of a library (R1) | ✅ |
| VI. Tests where the rule is subtle | Recurrence (24 months, short months, end date), overlap, conflict, isolation and offline ([quickstart](quickstart.md)) | ✅ |
| Product constraints | pt-BR (later English with a pt-BR translation), 360 px, keyboard and contrast kept. The due-date color uses the existing gradient | ✅ |
| Workflow | Spec with no open-question markers. Differences from the prototype are in the spec's assumptions section | ✅ |

**Re-check after Phase 1**: no violations. The contract only adds (the `/api/agenda` route and three operations) and changes no existing response, except for the new `due` field.

## Project Structure

### Documentation (this feature)

```text
specs/002-calendar-due-dates/
├── plan.md
├── research.md          # R1–R6
├── data-model.md
├── quickstart.md
├── contracts/api.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

Files touched (the structure is the one from 001):

```text
src/semana/
├── migrations/002_calendar.sql    # new: task.due, event table (now in 001_initial.sql)
├── reads.py                       # due in task_json; GET /api/agenda
├── ops.py                         # task.due, event.save, event.delete
└── static/
    ├── app.css                    # already has the calendar styles (copied in 001)
    └── js/
        ├── pure.js                # + occurrences, layoutEvents, weekday, monthShort, fmtDay
        ├── data.js                # + agenda(monday), with cache
        └── app.js                 # + due date, Calendar, editor, "On the agenda", event conflict

tests/
├── api/test_ops.py                # due date and event
├── api/test_agenda.py             # new
├── api/test_rollover.py           # due date kept and in the snapshot
├── api/test_isolation.py          # new cases
└── e2e/
    ├── test_recurrence.py         # new: occurrences and layoutEvents
    └── test_offline.py            # + event and due date with no network
```

**Structure Decision**: no new code files besides the migration. The calendar code goes back into `app.js`, where 001's T005 removed it from, with the prototype (`specs/semana.html`, lines 1581–1628 and 1116–1126) as the source.

## Complexity Tracking

No added dependency, layer or service.
