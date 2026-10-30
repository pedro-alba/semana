# Feature Specification: Single occurrences, duration by dragging and agenda summary

**Feature Branch**: `007-calendar-exceptions`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "Reduce the darkening of the cards in the Graphite theme. A card with no subtasks says nothing. All-day event with an option to fill the day's hours or not; with none in the strip, the 'All day' strip goes away. Recurring events show only once in the summary ('On the agenda'), with the recurrence spelled out. When dragging a recurring event, ask whether to change only that one or the series; the same when deleting. Change the duration by pulling the edge."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Only this occurrence or the series (Priority: P1)

**Acceptance Scenarios**:

1. **Given** an occurrence of a recurring event, **When** the person drags it (or pulls the edge) and drops it, **Then** the question "Change only this one or the whole series?" appears next to the event, with "Only this one", "Whole series" and "Cancel"; Esc or clicking outside cancels and the event goes back to its place.
2. **Given** "Only this one", **When** the person confirms, **Then** that date disappears from the series and a standalone event, with the same data and the new time, shows in its place; the other occurrences do not change.
3. **Given** "Whole series", **When** the person confirms, **Then** all occurrences shift (or change duration) by the same amount.
4. **Given** a recurring event opened from an occurrence, **When** the person asks to delete, **Then** they choose between "Only this one", "Whole series" and "Cancel"; "Only this one" removes only that date.
5. **Given** an event that does not repeat, **When** it is dragged or deleted, **Then** there is no series question (deleting asks for today's confirmation).

---

### User Story 2 - Change the duration by the edge (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a timed event, **When** the person pulls the bottom edge with the mouse, **Then** the end changes in 15-minute steps, with a minimum duration of 15 minutes, and is saved on drop (with the US1 question if it is recurring).

---

### User Story 3 - All day, filling the hours or not (Priority: P2)

**Acceptance Scenarios**:

1. **Given** "All day" checked in the editor, **When** the person looks at the form, **Then** "Fill the whole day" appears (unchecked by default).
2. **Given** the option checked, **When** the event is saved, **Then** it shows as a block from 00:00 to 24:00 on each day, in the hours grid, and not in the "All day" strip.
3. **Given** no event in the "All day" strip for the week (with the current visibility), **When** the calendar is drawn, **Then** the strip does not show.

---

### User Story 4 - Agenda summary without repetition (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a daily event, **When** the person looks at "On the agenda" for the current week, **Then** it shows once, at the next occurrence (the first one that has not ended yet; if all have passed, the last one of the week), with "Every day" and, if there is an end date, ", until 12/15".
2. **Given** other weeks, **When** the person looks at "On the agenda", **Then** the recurring event shows once, at the week's first occurrence.
3. **Given** a weekly event on Tuesdays and a monthly one on the 15th, **When** they show in the summary and in the details card, **Then** the recurrence reads "Every Tuesday" and "Every month on the 15th", with ", until …" when there is an end date.

---

### User Story 5 - Brighter, cleaner cards (Priority: P3)

**Acceptance Scenarios**:

1. **Given** the Graphite theme, **When** the person looks at the cards, **Then** the progress color looks more vivid (less darkened by the surface), keeping a 4.5:1 contrast with the text.
2. **Given** an open task with no subtasks, due date or carried-over weeks, **When** the person looks at the card, **Then** the line below the title is empty (it does not say "No subtasks").

### Edge Cases

- "Only this one" on a series that has only that occurrence in the week: the series still exists in the other weeks.
- Deleting "Only this one" on the last occurrence of a series with an end date: the series has no occurrences on that date; it stays editable.
- A standalone occurrence created by "Only this one" is a regular event: it can be edited, dragged and deleted with no series question.
- Pulling the edge of a block that continues into the next day: the edge only shows on the day the event ends.
- Dragging an "all day" event that fills the hours: it changes day, without changing time.
- Conflict and offline: as with any event edit (queue and revision from 002).

## Requirements *(mandatory)*

- **FR-001**: Dragging, pulling the edge and deleting a recurring event MUST ask "Only this one" or "Whole series", next to the event, with no modal window over the screen.
- **FR-002**: "Only this one" MUST remove the date from the series (list of skipped dates, stored with the event) and, when moving, create a standalone event with the series' data and the new time.
- **FR-003**: Pulling the bottom edge MUST change the end in 15-minute steps (minimum 15).
- **FR-004**: An all-day event MUST have the option "Fill the whole day"; checked, it shows in the hours grid; unchecked, in the "All day" strip, which only shows if it has something.
- **FR-005**: "On the agenda" MUST show each series once per week, as in US4, with the recurrence spelled out.
- **FR-006**: The details card MUST use the same recurrence text.
- **FR-007**: In Graphite, the progress color on cards MUST be stronger, with contrast ≥ 4.5:1 for the text over the blended color.
- **FR-008**: A task card with nothing to say MUST not have the "No subtasks" line.
- **FR-009**: Skipped dates and "fill the whole day" MUST be included in the backup (005) and in search (the next occurrence ignores skipped dates).

## Success Criteria *(mandatory)*

- **SC-001**: Moving or deleting a single occurrence takes one gesture and one choice.
- **SC-002**: A daily event takes one line in the week summary, not seven.
- **SC-003**: In every combination of theme, mode and gradient, card text keeps contrast ≥ 4.5:1.

## Assumptions

- Editing a recurring event in the editor still applies to the whole series (as in 002); the question is only for dragging, pulling the edge and deleting.
- The question shows as a small bubble next to the event (not modal; Esc cancels), in line with the constitution ("no modals").
- Deleting from the editor only offers "Only this one" when the editor was opened from an occurrence (click on the block or the summary); opened another way, the deletion applies to the series.
