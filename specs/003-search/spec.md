# Feature Specification: Search

**Feature Branch**: `003-search`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "Feature 003: search. Bring from the prototype (specs/spec.md v2.6, Search section; specs/semana.html, searchItems/rankSearch/snippetOf) to the multi-user app: Ctrl+Space opens the search box over the interface; it looks in titles, subtasks, task notes and week notes from every week and project in the account, ignoring case and accents; ranking, highlighted snippets and opening in the right place as in the prototype. User decision: on touch screens and on mobile, a magnifier icon in the header opens search (on desktop it stays the shortcut only, with the hint "Search Ctrl Space"). Respect isolated accounts and offline use."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find anything written, from any week (Priority: P1)

The person remembers a word ("résumé", "Joana") and wants to get to the task or notes where it is, without knowing which week or project they wrote it in.

**Why this priority**: with weeks and projects splitting the content, search is the only way to find something written long ago; it is the reason for the feature.

**Independent Test**: write titles, subtasks, task notes and week notes across several weeks and projects; search terms with and without accents, in capitals and with two words; open results of each kind.

**Acceptance Scenarios**:

1. **Given** any app screen on desktop, **When** the person presses Ctrl+Space, **Then** the search box opens in the center, over the interface, with the cursor in the field and, with no text, the most recently updated open tasks.
2. **Given** a task titled "Café with Joana", **When** the person types "cafe joana", **Then** the task shows among the results, already highlighted if it is the best one.
3. **Given** a term that appears only in the notes of a task from three weeks ago, in another project, **When** the person searches for it, **Then** the task shows with a snippet of the notes where the term is highlighted.
4. **Given** the highlighted result, **When** the person presses Enter (or clicks), **Then** the app goes to the result's week and project, opens the task (or the overview, for week notes) and selects the first occurrence of the term in the notes.
5. **Given** the open box, **When** the person presses Esc, Ctrl+Space or clicks outside, **Then** the box closes and focus goes back to where it was, including the cursor in the text being edited.

---

### User Story 2 - Search on mobile (Priority: P2)

On touch screens, with no physical keyboard, the person taps a magnifier in the header to open the same search.

**Why this priority**: mobile is first-class, but search is already useful without it.

**Independent Test**: on a 360 px touch screen, tap the magnifier, type a term, tap a result and check that it opens; on desktop with a mouse, check that the magnifier does not show and the shortcut hint does.

**Acceptance Scenarios**:

1. **Given** a touch screen or a phone, **When** the person looks at the header, **Then** they see the magnifier and do not see the "Search Ctrl Space" hint.
2. **Given** a desktop with mouse and keyboard, **When** the person looks at the header, **Then** they see the "Search Ctrl Space" hint and do not see the magnifier.
3. **Given** the magnifier, **When** the person taps it, **Then** the box opens as on desktop, with no sideways scrolling at 360 px.

---

### User Story 3 - Search offline and only in your own content (Priority: P2)

Search never shows anything from another account and keeps working, in a limited way, when the internet drops.

**Why this priority**: these are the feature 001 guarantees applied to search.

**Independent Test**: with two accounts using the same terms, check that each finds only its own content; offline, search a term from a week already opened and another from a week never opened on this device.

**Acceptance Scenarios**:

1. **Given** accounts A and B with the same term, **When** B searches for the term, **Then** only B's results show.
2. **Given** the connection is lost, **When** the person searches, **Then** they find what was already opened on this device, including changes not yet sent, and the box says the results are limited to that content.
3. **Given** a change made a moment ago (still pending or just sent), **When** the person searches for the new text, **Then** the result shows.

---

### Edge Cases

- No results: the box shows "Nothing found for “{term}”."
- No open tasks and an empty field: the box shows "No open tasks."
- Only spaces in the field: treated as an empty field.
- Term in a done subtask: the task is found (done subtasks are part of the content).
- Result in a closed week: opens the read-only snapshot and still selects the term, if it is in the notes.
- Task deleted after the search started: the result disappears on the next keystroke; opening it does not break the app.
- Empty week notes do not show as a result.
- Ctrl+Space with the box open: closes it.
- Ctrl+Space on a sign-in screen (no account): does nothing.
- Special terms (quotes, slashes, symbols): treated as plain text.

## Requirements *(mandatory)*

### Functional Requirements

#### Open and close

- **FR-001**: Ctrl+Space MUST open the search box from any app screen with a signed-in account, and close it if it is open.
- **FR-002**: A magnifier button (accessible label "Search tasks and notes") next to "+ New task" MUST open search on any screen. (Revised on 2026-10-29: replaces the "Search Ctrl Space" hint in the header and the touch-only magnifier, because in some browsers, such as Opera GX, Ctrl+Space belongs to the browser.)
- **FR-003**: The box MUST open in the center, over the interface, with the field focused; it closes with Esc, Ctrl+Space or a click outside, returning focus (and the cursor position in the text) to where it was. On opening, edits in progress are saved.
- **FR-004**: The box MUST be usable with the keyboard only and announced to screen readers as a search field with a results list; the footer shows "↑ ↓ choose", "Enter open" and "Ctrl+Space or Esc close".

#### Results

- **FR-010**: With no text, the list MUST show, under "RECENT", up to 8 of the most recently updated open tasks, from every week and project.
- **FR-011**: With text, search MUST look in the title, subtasks (pending and done) and notes of every task, and in week notes, from every week and project in the account, showing up to 10 results. It ignores case and accents; with more than one word, all must appear in the same result (in any of the fields).
- **FR-012**: The order MUST follow the prototype: title before content; a title equal to the term before a title that starts with it, and that one before a term in the middle of the title; then current week, future weeks and the most recent ones; done tasks below open ones with the same score.
- **FR-013**: Each result MUST show the progress color (task) or the notes icon (week notes), the title with the terms highlighted, project, week ("this week", "last week", "next week" or "week of {date}") and status (due date, as on the card, or "done"), a flag if important and, when some term only appears in the content, a snippet around the first occurrence with the terms highlighted.
- **FR-014**: The first result MUST come highlighted; the up and down arrows move the highlight (wrapping around); Enter or a click opens.
- **FR-015**: Opening a result MUST go to its week and project, open the task (or the overview, for week notes) and select and show the first occurrence of a term in the notes; in closed weeks, the content is the usual read-only view.
- **FR-016**: Results MUST reflect the current content, including changes made on this device and not yet sent.

#### Accounts and connection

- **FR-020**: Search MUST only consider content from the signed-in account (FR-005 from feature 001).
- **FR-021**: Offline, search MUST look in the content already available on this device and say so in the box: "Offline: results only from what was already opened on this device."

### Key Entities *(include if feature involves data)*

- **Search result**: a reference to a task or to the notes of a week + project pair, with title, project, week, status and snippet. Not stored.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With 2 years of typical use (about 1,500 tasks and 200 blocks of week notes), results show within 300 ms after the person stops typing, on a common broadband connection.
- **SC-002**: A person finds a task from months ago, of which they remember one word, in under 10 seconds from any screen.
- **SC-003**: In tests with accented terms, unaccented terms, capitals and several words, 100% of the expected results show, in the order set by FR-012.
- **SC-004**: Isolation tests with the same term in two accounts record zero results from another account.
- **SC-005**: The whole search (open, type, choose, open the result and close) can be done with the keyboard only on desktop and with touch only on a 360 px phone.

## Assumptions

- The reference behavior is the prototype's (specs/spec.md v2.6, Search section). Differences: the magnifier on touch screens (owner's decision, 2026-10-28), search over all of the account's content (not only what is loaded) and the offline notice.
- The search box is a layer over the interface, as in the prototype; the constitution's "no modals" rule is about tasks and forms, which stay in the content panel.
- Events (feature 002) are not searched, as in the prototype.
- The content of closed-week snapshots is not searched separately: search finds the live task and, if it is in a closed week, opens the snapshot.
- Exact-phrase search, filters, operators and search history are out of scope.
