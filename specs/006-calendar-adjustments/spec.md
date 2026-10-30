# Feature Specification: Calendar adjustments, project memory and event search

**Feature Branch**: `006-calendar-adjustments`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "Calendar fixes. When creating an event: the end date changes by itself if it ends up before the start; description right below the title; frequency with 'every day' and 'once' as the default; 'repeat until' below the frequency, only when it is no longer 'once'. In the calendar: drag the event; on mouse hover, a card with details without opening the editor. The app remembers the last Project choice in Tasks and in the Calendar. Search includes events; when one is picked, it goes to the calendar with the event highlighted." Owner's decisions (2026-10-29): dragging moves the whole series; "repeat until" is optional and, with no date, the recurrence does not end; the project choice is remembered per device; in search, a recurring event leads to the next occurrence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and edit events with less friction (Priority: P1)

**Independent Test**: create one-off, daily, weekly and monthly events, with and without an end date, moving the start to after the end.

**Acceptance Scenarios**:

1. **Given** the editor, **When** the person looks at the form, **Then** the order is: Title, Description, All day, Start, End (or Last day), Frequency, Repeat until (when visible), Project, Location.
2. **Given** a start and an end, **When** the person moves the start to after the end, **Then** the end becomes the new start plus the duration the event had; if the end is still after the start, nothing changes.
3. **Given** a new event, **When** the editor opens, **Then** the frequency is "Once" and "Repeat until" does not show.
4. **Given** the frequency "Once", **When** the person picks "Every day", "Every week" or "Every month, same day", **Then** "Repeat until · optional" appears right below; going back to "Once" hides it and the date is discarded.
5. **Given** "Every day" with no end date, **When** the person saves, **Then** the event shows every day from the start, in any future week.

---

### User Story 2 - See and move events right in the grid (Priority: P1)

**Independent Test**: with a mouse, hover over an event and check the card; drag a one-off and a recurring event to another day and time.

**Acceptance Scenarios**:

1. **Given** an event in the grid, **When** the mouse pointer rests on it (or it gets keyboard focus), **Then** a card appears beside it with title, day and time (or "All day"), frequency and end date, project, location and the start of the description, without opening the editor; the card goes away when the pointer or focus leaves.
2. **Given** a timed event, **When** the person drags it to another day or time, **Then** it moves in 15-minute steps, keeping its duration, and is saved on drop.
3. **Given** an all-day event, **When** the person drags it in the "All day" strip to another day, **Then** it changes day, keeping its duration.
4. **Given** a recurring event, **When** the person drags an occurrence, **Then** the whole series shifts by the same amount (day and time); the recurrence end date, if any, shifts too when it would fall before the new start.
5. **Given** a click without dragging, **When** the person releases, **Then** the editor opens as today.
6. **Given** a touch screen, **When** the person taps the event, **Then** the editor opens as today (dragging and the details card are for the mouse).

---

### User Story 3 - The app remembers the project (Priority: P2)

**Acceptance Scenarios**:

1. **Given** Work picked in Tasks, **When** the person reloads or comes back another day on this device, **Then** Tasks opens on Work.
2. **Given** "Personal" picked in the Calendar's Visibility, **When** the person comes back to the Calendar (including after a reload), **Then** the visibility is Personal.
3. **Given** a remembered project that was deleted, **When** the app opens, **Then** the first project applies (Tasks) or "All projects" (Calendar).
4. **Given** another account in the same browser, **When** it logs in, **Then** it uses its own choices, not the previous account's.

---

### User Story 4 - Find events in search (Priority: P2)

**Acceptance Scenarios**:

1. **Given** an event "English class" with location "School", **When** the person searches "english" or "school", **Then** the event appears, with a calendar icon, the project and the occurrence date.
2. **Given** the picked result, **When** the person presses Enter or clicks, **Then** the app goes to the Calendar on the occurrence's week (the next one from today; if the series ended, the last one; if it is a one-off, its own), scrolls to it, focuses it and shows the details card.
3. **Given** the Calendar's visibility filtering another project, **When** the person opens an event from search, **Then** the visibility switches to "All projects" so that it shows.

---

### Edge Cases

- Dragging outside the grid: it goes back to its place, without saving.
- Dragging past midnight: the start is limited to the day (00:00–23:45); events that cross midnight can still exist through the editor.
- Dragging with no connection: it saves locally and goes through the queue, like any edit.
- Conflict (the event was changed on another device): the conflict warning from 002 appears, as with an edit in the editor.
- Monthly event on the 31st: only shows in months that have a 31st (as today).
- "Every day" series with no end date in a distant week: shows normally.
- Details card near the screen edge: stays inside the window.
- Search with no connection: events from the index stored on the device, like tasks.
- Closed weeks: events are not read-only (as today).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The editor MUST follow the order of scenario 1.1.
- **FR-002**: Moving the start to after the end MUST move the end, keeping the previous duration.
- **FR-003**: Frequency MUST have "Once" (default), "Every day", "Every week" and "Every month, same day"; "Repeat until · optional" only shows, below it, with a frequency other than "Once".
- **FR-004**: A recurrence with no end date MUST continue indefinitely; "every day" MUST produce one occurrence per day from the start.
- **FR-005**: With a mouse, hovering over an event (or focusing it by keyboard) MUST show the details card of scenario 2.1.
- **FR-006**: With a mouse, dragging MUST move the event (or the whole series) in 15-minute steps in the grid and one-day steps in the all-day strip, saving on drop through the usual queue.
- **FR-007**: The app MUST remember, per device and per account, the last project in Tasks and the last visibility in the Calendar.
- **FR-008**: Search MUST look in the title, location and description of the account's events and open the result as in scenario 4.2.
- **FR-009**: Everything stays isolated per account and works offline like the rest of the calendar.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Creating a weekly event takes at most one field more than a one-off (the frequency).
- **SC-002**: Moving an event to another day and time takes one gesture (drag and drop).
- **SC-003**: In 100% of the app's openings on this device, the project and the visibility are the ones from last time.
- **SC-004**: An event is found by search by title, location or description, ignoring accents and case.

## Assumptions

- Dragging and the details card are for the mouse (and pen); on touch, tapping opens the editor, as today.
- Resizing by the edge (changing the duration by dragging) is out of scope; the duration changes in the editor.
- The project memory lives in browser storage, separate per account; it does not go to the server.
- With an empty search field, the recent list still has only tasks.
