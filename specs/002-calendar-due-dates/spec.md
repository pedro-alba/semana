# Feature Specification: Calendar and due dates

**Feature Branch**: `002-calendar-due-dates`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "Feature 002: calendar and due dates. Bring from the prototype (specs/semana.html, spec v2.6 in specs/spec.md) to the multi-user app from feature 001: due dates on tasks (independent of the week, kept through the rollover, shown on cards), events with recurrence (Calendar screen, side editor on desktop and stacked on mobile), and the "On the agenda" section in the overview. Respect isolated accounts, offline use and the conflict handling from feature 001."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Give a task a due date (Priority: P1)

The person sets when a task must be done. The due date shows on the card and in the document, warns when it has passed, and stays with the task when it moves to the next week.

**Why this priority**: the due date is the smallest addition that changes day-to-day decisions, and it does not depend on the calendar screen.

**Independent Test**: set due dates of today, tomorrow, another day this week, a future date and a past date on open tasks, finish one of them, simulate the rollover, and check the card texts and that the due date is kept.

**Acceptance Scenarios**:

1. **Given** an open task, **When** the person uses the "Due date" button on the line below the title and picks a date, **Then** the due date shows in the document and on the card and is still there after a reload.
2. **Given** open tasks with due dates, **When** the person looks at the list, **Then** each card shows "due today", "due tomorrow", "due <weekday>" (same week) or "due <month> <day>"; with a past due date, "was due <month> <day>" in red.
3. **Given** a finished task with a due date, **When** the person looks at the list, **Then** the card does not show the due date.
4. **Given** an open task with a due date, **When** the rollover carries it over, **Then** the due date stays the same.
5. **Given** a task with a due date, **When** the person uses the due date's ×, **Then** the due date is removed.

---

### User Story 2 - See and add events in the week (Priority: P1)

On the Calendar screen, the person sees the week as a grid, creates events by clicking a time slot or the button, and marks meetings that repeat every week or every month.

**Why this priority**: it is the other half of the prototype's weekly planning; without it, the person goes back to a separate calendar.

**Independent Test**: create a one-off event, a multi-day all-day event, a weekly event with an end date, and a monthly event on the 31st; browse several weeks and months and check the occurrences; edit and delete the series.

**Acceptance Scenarios**:

1. **Given** the Calendar screen, **When** the person opens it, **Then** they see the Monday-to-Sunday grid, from 00:00 to 24:00, scrolled to 07:00, with the "Agenda" header, the "All day" band and all projects.
2. **Given** the grid, **When** the person clicks an empty time slot or "+ New event", **Then** the editor opens (beside the grid on desktop, stacked on mobile) starting at that time and ending one hour later.
3. **Given** a weekly event with an end date, **When** the person browses the weeks, **Then** each occurrence shows on the same weekday and time, up to and including the end date, and none after it.
4. **Given** a monthly event on the 31st, **When** the person browses February and April, **Then** those months have no occurrence.
5. **Given** an event in a series, **When** the person edits or deletes it, **Then** the change applies to the whole series, and deleting asks for confirmation inside the editor.
6. **Given** two events at the same time, **When** the grid is shown, **Then** they appear side by side in columns.
7. **Given** the project filter, **When** the person picks a project, **Then** only that project's events and due dates are shown.

---

### User Story 3 - Due dates in the calendar and "On the agenda" (Priority: P2)

Task due dates show in a band of the calendar, and the overview gains "On the agenda", with the week's due dates and events and the overdue ones at the top.

**Why this priority**: it brings the two previous stories together where the person picks the work back up; it depends on both.

**Independent Test**: with due dates and events in several projects and a task whose due date passed last week, open the overview and the calendar for the current week and check order, labels and links.

**Acceptance Scenarios**:

1. **Given** a week with due dates, **When** the person opens the calendar, **Then** the "Due dates" band shows above "All day", with each due date in its progress color; overdue ones in red and those of finished tasks struck through.
2. **Given** a due date in the calendar, **When** the person clicks it, **Then** the task opens in its own week and project.
3. **Given** the overview of the current week, **When** there are due dates and events, **Then** "On the agenda" lists, across all projects, open-task due dates before the events of the same day, with day, time (or "due") and project, and overdue due dates from earlier weeks at the top as overdue.
4. **Given** an item in "On the agenda", **When** the person activates it, **Then** a due date opens the task and an event opens the editor in the calendar.

---

### User Story 4 - Calendar offline and across devices (Priority: P2)

Events and due dates follow the same guarantees as tasks: they stay in the person's account only, can be created and changed offline, and are never overwritten silently.

**Why this priority**: feature 001 already set these guarantees; the calendar cannot be the exception.

**Independent Test**: offline, create an event and change a due date, close and reopen the tab, reconnect and check on another device; edit the same event on two devices and check the warning.

**Acceptance Scenarios**:

1. **Given** the connection is lost, **When** the person creates, edits or deletes events and due dates in weeks already loaded, **Then** the changes stay pending in the footer and are sent in order on reconnect.
2. **Given** an event changed on another device after the editor was opened, **When** the person saves, **Then** they are warned and choose which version to keep; the other stays available to copy until the warning is closed.
3. **Given** accounts A and B, **When** B tries to read or change A's events, including by direct address, **Then** access is denied as if the event did not exist.

---

### Edge Cases

- End equal to or before the start: the event is not saved and the editor explains why.
- Duration over 31 days: the event is not saved.
- Event that crosses midnight: shows on both days, cut at each day's edge.
- All-day event: the editor shows the last day (inclusive); the event spans from the first to the last day.
- Series with no end date from earlier versions: the editor warns that leaving "Repeat until" blank ends the recurrence on save.
- Clearing "Repeat until": recurrence is turned off and the event becomes a one-off.
- End date before the start: the event is not saved.
- Task due date in a closed week: the snapshot keeps the due date as it was; the calendar shows the task's current due date.
- Deleted task: the due date disappears from the calendar and the agenda.
- A task that is fully blank except for the due date is not discarded when leaving it.
- "Location or link" with an address or file path: a button opens the address (or copies the path, as with links in notes).
- Calendar of past weeks: events stay editable; due dates show as they are on the tasks.
- Offline, opening a week in the calendar that was not loaded: a notice that a connection is needed.

## Requirements *(mandatory)*

### Functional Requirements

#### Due dates

- **FR-001**: Users MUST be able to set, change and remove an optional due date per task: a date, with no time, through the "Due date" button on the line below the document title; the × removes it. In closed weeks, the due date is only shown.
- **FR-002**: The due date MUST be independent of the task's week: it does not move the task, does not mark it important, and is kept by the rollover.
- **FR-003**: The card of an open task with a due date MUST show "due today", "due tomorrow", "due <short weekday>" (in the same week as today) or "due <short month> <day>"; a due date before today shows "was due <short month> <day>" in red. Cards of finished tasks do not show the due date. A due date does not reorder cards.
- **FR-004**: The document's info line MUST show the due date after project, week and weeks open.
- **FR-005**: Setting, changing or removing the due date MUST count as an update for "Worth picking up".
- **FR-006**: A task with a due date MUST NOT be considered blank (complements FR-028 from feature 001).
- **FR-007**: The weekly snapshot MUST keep each task's due date as it was when the week closed.

#### Calendar

- **FR-010**: The header MUST gain the "Calendar" navigation next to "Tasks". The week navigation from feature 001 also applies in the calendar; there, going back to the current week only changes the week.
- **FR-011**: The Calendar screen MUST show the "Agenda" header, the "+ New event" button, the project filter (starts at "All projects") and a Monday-to-Sunday grid, from 00:00 to 24:00, initially scrolled to 07:00, with a "Due dates" band (only when there are any) and an "All day" band. Today is highlighted. On desktop, the page fits the window and only the grid and the editor scroll.
- **FR-012**: Overlapping events MUST be laid out in side-by-side columns. Events that cross midnight show on each day, cut at the day's edge. Recurring events show the ↻ marker.
- **FR-013**: The project filter MUST apply to the calendar's events and due dates.

#### Events

- **FR-020**: Users MUST be able to create events through the button (start today if the shown week is the current one, or on the Monday of the shown week, at 09:00) or by clicking an empty time slot (start at that time); the default end is one hour after the start, capped at the end of the day.
- **FR-021**: An event MUST have a title (required, up to 160 characters), a start and end (date and time) or all day (first and last day), an optional project ("No project"), an optional "Location or link" and an optional plain-text description.
- **FR-022**: The end MUST be after the start, with a maximum duration of 31 days; violations block saving and are explained in the editor.
- **FR-023**: "Repeat until" (optional date, inclusive) MUST turn on recurrence when filled in and only then show "Frequency": "Every week" (default) or "Every month, same day". Clearing the date turns recurrence off. The end date cannot be before the start.
- **FR-024**: Weekly recurrence MUST keep the weekday and time; monthly recurrence MUST keep the day of the month, and months without that day get no occurrence. There are no single-occurrence exceptions: edits and deletes apply to the whole series, and the editor says so.
- **FR-025**: The editor MUST sit beside the grid on desktop and stacked on smaller screens, with no modal. It closes with × or Esc. Deleting asks for confirmation inside the editor ("Delete this event?" or "Delete the whole series?").
- **FR-026**: When "Location or link" holds a web address, e-mail or file path (same rules as FR-037 from feature 001), the field MUST gain a button to open it, or to copy the path in the case of files.
- **FR-027**: Events MUST NOT be linked to tasks and MUST NOT change with the weekly rollover.

#### Due dates in the calendar and "On the agenda"

- **FR-030**: The "Due dates" band MUST show, on each day, the due dates of tasks (open and finished) for that day, with the progress color and the title; overdue ones of open tasks in red and those of finished tasks struck through. Order: open before finished, important first, then title.
- **FR-031**: Activating a due date, in the calendar or in "On the agenda", MUST open the task in its own week and project.
- **FR-032**: The overview MUST gain the "On the agenda" section, with open-task due dates and events of the shown week, across all projects, sorted by day; on the same day, due dates before events. Each item shows day, time (or "Due"/"Overdue"), title and project. In the current week, open-task due dates that passed before the week show at the top as overdue. Up to 9 items are shown and the "View week ↗" link opens the calendar. With no items, it shows "No due dates or events this week."
- **FR-033**: Activating an event in "On the agenda" MUST open the calendar on that week with the event's editor.

#### Accounts, connection and conflicts

- **FR-040**: Events and due dates MUST follow the account rules from feature 001: they belong to the signed-in account, are invisible to other accounts (FR-005) and are removed when the account is deleted (FR-006).
- **FR-041**: Offline, creating, editing and deleting events and setting due dates MUST work on content already loaded, with the changes kept on the device and sent in order on reconnect (FR-056 from feature 001); opening a week that was not loaded shows the connection notice (FR-057).
- **FR-042**: If an event was changed or deleted on another device after the editor loaded it, saving MUST NOT overwrite silently: the person is warned and chooses which version to keep; the one not chosen stays available to copy until the warning is closed. The event is treated as one unit. Due dates follow "last write wins", like progress and importance.
- **FR-043**: Events MUST be shown in the account's time zone; times are local, as in the prototype.

### Key Entities *(include if feature involves data)*

- **Due date**: optional date on the task (no time), part of the Task from feature 001.
- **Event**: belongs to an account; title, start, end, all day, optional project, location or link, description, recurrence (none, weekly or monthly) and end date. Not linked to tasks.
- **Occurrence**: each appearance of an event in a week, derived from the recurrence; not stored.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A person sets a task's due date in at most 3 interactions from the open document.
- **SC-002**: A person creates a weekly event in under 30 seconds from the Calendar screen.
- **SC-003**: In recurrence tests covering 24 months (including February, 30-day months, leap years and the turn of the year), 100% of the expected occurrences appear and no wrong occurrence appears.
- **SC-004**: The calendar of a week with 50 events and 30 due dates is usable within 1 second after changing weeks on a common broadband connection.
- **SC-005**: Isolation tests covering every event and due date operation record zero accesses to another account's data.
- **SC-006**: In connection-loss tests with the tab closed and reopened, 100% of the events and due dates changed during the outage are saved and visible on another device after reconnecting.
- **SC-007**: Every flow in this feature can be completed with the keyboard only and on a phone with a 360 px wide screen.

## Assumptions

- The reference behavior is the prototype's (specs/spec.md v2.6, sections on due dates, the calendar and the overview). The differences are: per-account data, sync across devices, conflict warning on events (FR-042) and the rule that a due date keeps a "blank" task from being discarded (already in the prototype).
- Event times are local to the account's time zone; changing the time zone is out of scope (as in feature 001).
- The calendar of past weeks stays editable: events are not snapshotted and do not become read-only. The due dates shown are the tasks' current ones.
- "On the agenda" and the calendar show due dates from all projects, including weeks other than the task's week.
- Still out of scope: notifications and reminders, invitations and attendees, integration with Google Calendar or Outlook (.ics import/export), single-occurrence recurrence exceptions, a time on the due date, a due date that moves the task's week, links between events and tasks, and dragging events on the grid.
- Search (003), appearance (004) and import/backup (005) stay in their own features; importing prototype backups will bring events and due dates.
