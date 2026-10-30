# Implementation Plan: Single occurrences, duration by dragging and agenda summary

**Branch**: `007-calendar-exceptions` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

## Summary

- **Server**: the migration `005_event_extra.sql` (later folded into `001_initial.sql`) adds two columns to `event`:
  - `fills_day INTEGER NOT NULL DEFAULT 0`
  - `skipped TEXT NOT NULL DEFAULT '[]'`, with the JSON list of skipped dates.

  Both fields go into `event.save` (which still writes the whole record, with the same revision), into `event_json` and, therefore, into the agenda, search and backup.
- **Client**:
  - `occurrences` skips the dates in `skipped`.
  - "Only this one" is the series saved with one more date in `skipped`, plus a new standalone event, created with `event.save` and `base_rev` 0. These are two ops in the usual queue.
  - Dragging (006) gains the "resize" mode and, for a series, a question bubble before saving.
  - The summary groups by series.
  - A pure function, `repeatText(e)`, builds the recurrence text.

## Constitution Check

| Principle | How it complies | Status |
| --- | --- | --- |
| I. Fewer controls | The bubble only shows for recurring events. The "All day" strip goes away when empty | ✅ |
| III. Nothing is lost | Cancel in the bubble puts the event back. The two ops of "Only this one" go through the queue. Conflict through the record's revision | ✅ |
| IV. Isolated accounts | No new route. The new columns follow the existing `account_id` filter | ✅ |
| V. Simplicity | Skipped dates in a JSON column on the series itself, instead of an exceptions table. "Only this one" reuses event creation | ✅ |
| "No modals" constraint | Bubble next to the event, not modal | ✅ |

## Decisions

- **R1. Skipped dates on the series.** A list of dates (`YYYY-MM-DD`, up to 1,000) on the row itself, written along with the rest by `event.save`. Moving "Only this one" keeps no link to the series: the standalone event is independent, as in Google Calendar when an occurrence is split off.
- **R2. Question bubble.** A `#series-pop` positioned next to the block, with three buttons and focus on the first. Esc or a click outside cancels and redraws. Deleting "Only this one" uses the occurrence date stored in `draft.occurrence`, which comes from the block's or summary row's `data-occ`.
- **R3. Edge.** A `<span class="resize">` at the bottom of the block, only on the day the event ends. Dragging it changes only `end`.
- **R4. Contrast in Graphite.** The contrast test now blends the gradient's strongest layer (the left one) over `--surface` before measuring.

## Project Structure

```text
src/semana/migrations/005_event_extra.sql  # now part of 001_initial.sql
src/semana/ops.py, reads.py, backup.py
src/semana/static/js/pure.js         # occurrences with skipped; repeatText; nextOccurrence
src/semana/static/js/app.js          # editor, summary, bubble, edge, all day in the grid, task card
src/semana/static/app.css
tests/api/test_ops.py, test_backup_api.py
tests/e2e/test_recurrence.py, test_calendar_007.py, test_appearance_panel.py
```
