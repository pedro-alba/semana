# Feature Specification: Accounts and weekly core

**Feature Branch**: `001-accounts-weekly-core`

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "Turn the Semana prototype (specs/semana.html, specification v2.6 in specs/spec.md) into a working multi-user app: individual, private accounts, open sign-up, tolerant of dropped connections. This slice covers accounts and the weekly core: tasks, subtasks, notes, rollover and overview."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Have my Semana on any device (Priority: P1)

A person creates their own account with e-mail and password and then finds their tasks and notes in any browser where they log in. No one else sees what they write.

**Why this priority**: it is what turns the local prototype into a multi-user product; nothing else works without an account.

**Independent Test**: create account A, create a task, log out, log in from another browser and see the task; create account B and confirm it sees nothing from A.

**Acceptance Scenarios**:

1. **Given** a visitor without an account, **When** they sign up with a valid e-mail and password, **Then** they are logged in right away and see the Personal project, the current week and an empty overview.
2. **Given** an account with tasks, notes and a set order, **When** the person logs in on another device, **Then** they see the same data, in the same order.
3. **Given** accounts A and B, **When** B tries to access any of A's data, including by direct address, **Then** access is denied as if the data did not exist.
4. **Given** a person who forgot their password, **When** they ask for recovery, **Then** they get by e-mail a single-use, time-limited link, set a new password, and their other sessions are ended.
5. **Given** a logged-in person, **When** they log out, **Then** they go back to the login screen and the data is no longer visible on that device.
6. **Given** a logged-in person, **When** they delete the account confirming with the password, **Then** the account and all its data are removed and the e-mail is free for a new sign-up.

---

### User Story 2 - Plan and track the week's tasks (Priority: P1)

The person picks a project and a week, creates tasks, adjusts progress by dragging the card, marks importance and rearranges the list in any order they like.

**Why this priority**: it is the product's daily use.

**Independent Test**: create tasks in Personal in the current week and in a future week, adjust progress until done, reorder, reload the page and check that everything persists.

**Acceptance Scenarios**:

1. **Given** the current week in Personal, **When** the person clicks "+ New task", **Then** the task is created at 0% at the end of the open tasks and opens with the title focused.
2. **Given** a task created in a future week, **When** the person goes back to the current week, **Then** the task does not show up there.
3. **Given** a new project created with the + button, **When** it is selected, **Then** it shows only its own tasks.
4. **Given** a selected card, **When** the person drags it sideways, **Then** the color changes with the progress; a simple tap changes nothing; on reaching 100% the task moves to the end of Done.
5. **Given** a list with several open tasks, **When** the person drags a card up (mouse), holds and drags (touch) or uses Alt + arrow (keyboard), **Then** the new position persists after reloading.
6. **Given** a task open in the panel, **When** the person presses Esc or clicks the card again, **Then** they go back to the overview of the displayed week without changing the progress.

---

### User Story 3 - Write in the task like in a document (Priority: P1)

The open task is a document: title, subtasks, notes with simple formatting and links, and a log of what was done or carried over.

**Why this priority**: replacing the document full of highlights is Semana's reason to exist.

**Independent Test**: open a task, format text, paste a passage from Google Docs, create and complete subtasks, add a website link and a file path, reload and check everything.

**Acceptance Scenarios**:

1. **Given** an open task, **When** the person applies bold, italic, sizes, highlight, list and link, **Then** the formatting persists after reloading.
2. **Given** a passage copied from Google Docs with highlights, links, colors and fonts, **When** it is pasted into the notes, **Then** highlights and links stay, and colors, fonts and images are dropped.
3. **Given** a pending subtask, **When** the person completes it, **Then** it moves to the log with the completion date and can be undone; in the log, it can be reopened or deleted.
4. **Given** text being typed, **When** the person stops typing, **Then** the text is saved with no extra action.
5. **Given** a Windows file path pasted with "Copy as path", **When** it becomes a link, **Then** the popover offers "Copy path" with instructions on where to paste it.
6. **Given** the trash can in the task bar, **When** the person uses it, **Then** deletion happens only after confirming in the bar itself.

---

### User Story 4 - Weekly rollover (Priority: P2)

On Monday, what was left open moves to the new week, at the top of the list, and the closed week is kept as a read-only snapshot.

**Why this priority**: without rollover the week model does not hold, but the app is usable for a few days without it.

**Independent Test**: with open and done tasks in a week, simulate the passing of one and of several weeks and check carry-overs, the counter, the log and the snapshots.

**Acceptance Scenarios**:

1. **Given** open and done tasks in the closed week, **When** the rollover happens, **Then** the done tasks stay in the original week and the open ones go to the top of the next week, in the order they were in, with everything preserved and the weeks-open counter incremented.
2. **Given** a person away for three weeks, **When** they come back to the app, **Then** each week in between is processed exactly once.
3. **Given** the same account open on two devices at the time of the rollover, **When** both detect it, **Then** there is no duplicate carry-over.
4. **Given** a closed week, **When** the person opens it, **Then** they see the snapshot in read-only mode.

---

### User Story 5 - Lose nothing when the connection drops (Priority: P2)

If the internet drops mid-writing, the person keeps writing. The footer shows that changes are waiting, and they are sent when the connection comes back.

**Why this priority**: the "nothing gets lost" principle now depends on the network; without this, the hosted app is worse than the local prototype.

**Independent Test**: with a task open, turn off the network, edit title, notes and subtasks, close and reopen the tab, turn the network back on and check that everything arrived and shows up on another device.

**Acceptance Scenarios**:

1. **Given** a lost connection, **When** the person keeps editing what is on screen, **Then** the footer shows it is offline and how many changes are waiting to be sent.
2. **Given** pending changes, **When** the connection comes back, **Then** they are sent in the order they were made and the footer goes back to "saved".
3. **Given** pending changes, **When** the tab is closed and reopened on the same device, **Then** the pending changes are still stored and get sent.
4. **Given** pending changes, **When** the person tries to log out, **Then** they are warned that the changes will be discarded and must confirm.

---

### User Story 6 - Overview and week notes (Priority: P3)

With no task open, the panel shows what matters in the week: free-form notes, pending subtasks and stalled tasks.

**Why this priority**: it speeds up picking things back up, but the app works with the list and the document.

**Independent Test**: write week notes, create subtasks in several tasks, leave a task without updates for 72 hours and check the overview.

**Acceptance Scenarios**:

1. **Given** no task selected, **When** the person looks at the panel, **Then** they see the week notes, pending subtasks of open tasks and "Worth picking up", without repeating the list of cards.
2. **Given** written week notes, **When** the week rolls over, **Then** they stay in the week they were written in, read-only.
3. **Given** an open task without updates for 72 hours, **When** the person sees the overview, **Then** the task shows up in "Worth picking up"; rearranging it or carrying it over does not take it off.

---

### Edge Cases

- The same task or the same week notes are edited on two devices at the same time, or a device comes back from an outage with edits to a text that changed elsewhere: whoever saves later is warned and chooses which version to keep (FR-061).
- The session expires while the person is typing: the text is not lost; they log in again and the pending changes are sent.
- Another account logs in on the same device while the previous account has pending changes: those changes are never sent to the other account.
- Offline, the person tries to open a week or project that was not loaded yet: the app warns that it needs a connection for that.
- A task left completely blank (no title, notes, subtasks, progress or importance): it is discarded when the person leaves it.
- "+ New task" in a past week: the task goes to the current week.
- Deleting a task that appears in snapshots of closed weeks: the snapshots are preserved.
- Sign-up with an e-mail already in use: the sign-up is refused with guidance to recover the password.
- Recovery request for an e-mail that does not exist: the response is the same as for an existing e-mail.
- Many wrong login attempts: new attempts are blocked temporarily.
- Content pasted or saved with scripts, styles or dangerous addresses: it is dropped before saving and before displaying.
- File path with ~: the app asks for the full path.

## Requirements *(mandatory)*

### Functional Requirements

#### Accounts and access

- **FR-001**: The system MUST let anyone create an account with an e-mail and a password of at least 8 characters, without an invitation.
- **FR-002**: Users MUST be able to log in and log out; the session stays active on the device until logging out or after 30 days without use.
- **FR-003**: Users MUST be able to reset the password through a link sent to their e-mail, single-use and valid for 1 hour; the response to the request does not reveal whether the e-mail has an account; resetting ends the other sessions.
- **FR-004**: The system MUST temporarily block login after repeated wrong attempts.
- **FR-005**: The system MUST restrict every read and change of data to the authenticated account; attempts to access another account's data respond as if the data did not exist.
- **FR-006**: Users MUST be able to delete the account, confirming with the password; all the account's data is permanently removed.
- **FR-007**: A new account MUST start with the Personal and Work projects, no tasks, Personal selected in the current week and the overview open. The account's time zone is the one of the device used to sign up.

#### Structure and navigation

- **FR-010**: The header MUST have the "semana." brand, the Tasks navigation and the profile icon, which shows the account e-mail and the Log out and Delete account actions. The footer MUST show the save state and the phrase "One day at a time."
- **FR-011**: On desktop, the task list MUST take about 25% of the width and the content the rest, fitting the window height with inner scrolling; on smaller screens, list and content stack. No modals.
- **FR-012**: Projects MUST be flat groupings; users can create projects with the + button next to the selector, with a required name.
- **FR-013**: Week navigation MUST have four controls of the same size: previous week, next week, pick a week and back to the current week. Going back to the current week and clicking the brand close the open task and show the overview of the current week.
- **FR-014**: Past weeks MUST show the PAST label; future weeks, PLANNING; the current week, none.
- **FR-015**: Switching project or week MUST go back to the overview. Closing the task (Esc with no menu, form or popover open, or a new click on the open card) MUST go back to the overview of the displayed week and return focus to the card.

#### Task list

- **FR-020**: Each card MUST show the title, the number of pending subtasks, how many weeks it has been open when it came from earlier weeks ("↪ week 2") and a red flag if important. The card color shows progress through the Classic gradient (0% RGB(244,247,251), 50% RGB(123,184,247), 100% RGB(124,216,173), linear interpolation); there is no visible number or bar, and the percentage is announced to screen readers.
- **FR-021**: Open tasks MUST sit above "Done"; within each group the user-defined order applies. Importance does not reposition cards.
- **FR-022**: The gradient legend MUST sit at the bottom of the column, outside the scrolling area, with the gesture hint and a marker for the selected task.
- **FR-023**: Users MUST be able to reorder cards within the same group: dragging with the mouse, holding about 0.35 s and dragging on touch (swiping without holding scrolls the list), and with Alt + arrow on the keyboard. The card follows the pointer, the others make room and the list scrolls on its own near the edges. Past weeks cannot be rearranged.
- **FR-024**: A new task MUST go to the end of the open tasks; when done, it goes to the end of Done; when reopened, to the end of the open tasks.
- **FR-025**: Users MUST be able to adjust progress by dragging the selected card horizontally, relative to the start of the gesture and only after a few pixels; a simple tap changes nothing. With the keyboard, the left and right arrows adjust by 5% (with Shift, 10%). 100% moves the task to Done; lowering it returns it to the open tasks. Progress and subtasks are independent.
- **FR-026**: Importance MUST be binary, toggled by the flag in the task bar.
- **FR-027**: "+ New task" MUST create the task in the displayed project and week, at 0%, and open it with the title focused; in a past week, the task goes to the current week. A task's week does not change after creation, except through the rollover.
- **FR-028**: A completely blank task MUST be discarded when the person leaves it.

#### Task document

- **FR-030**: The open task MUST fill the content panel as a single document, in a centered reading column, in this order: fixed bar, title editable in place (Enter moves to the notes), line with progress color, project, week and weeks open, pending subtasks followed by the "New subtask" field, notes, and log (when there is one). Clicking empty space puts the cursor in the notes.
- **FR-031**: The bar MUST have bold, italic, size (Heading, Subheading, Text), highlight, list and link and, on the right, flag and trash can. There is no × button to close: the current-week button, Esc and a new click on the card already do that (a departure from the prototype). With a mouse, formatting, flag and trash can show up only while the pointer is over the task or during editing; on touch, they are always visible. In closed weeks, the bar shows only the read-only notice.
- **FR-032**: The editor MUST accept the shortcuts Ctrl/Cmd+B (bold), Ctrl/Cmd+I (italic), Ctrl/Cmd+Shift+H (highlight), Ctrl/Cmd+Shift+8 (list), Ctrl/Cmd+K (link) and Ctrl/Cmd+Alt+1, 2 and 0 (Heading, Subheading, Text).
- **FR-033**: Title and notes MUST be saved while typing; when switching task or screen, or when the tab is hidden, pending changes are sent right away.
- **FR-034**: The trash can MUST ask for confirmation in the bar itself before deleting. Deleting preserves the snapshots of closed weeks.
- **FR-035**: Notes MUST limit formatting to bold, italic, three sizes, highlight, bulleted list and links. Pasting from other editors keeps those elements and drops the rest (fonts, colors, arbitrary sizes, images). The highlight does not store a color; the displayed color comes from the appearance.
- **FR-036**: All rich content MUST be sanitized on save and on display: nothing that runs code, loads external resources or changes the page; links accept only http, https, mailto and file.
- **FR-037**: The link form MUST have "Address or file path" and "Display text" and apply the link to the selection, if any. It accepts web addresses with or without protocol, e-mail, and Windows file paths (including quoted ones), network paths (\\server\folder) and macOS/Linux paths, stored as file:// addresses; paths with ~ ask for the full path. Without display text, the link shows the shortened address or the file name. Pasting an address or path on its own creates the link; with a selection, it turns the selection into a link.
- **FR-038**: With the cursor over a link, a popover MUST show the target and the Open, Edit and Remove actions; Ctrl/Cmd+click opens it directly; in read-only mode, one click opens it. Web links open in a new tab. File links have a dotted underline and a document icon, and Open is replaced by "Copy path" with instructions on where to paste it (File Explorer; on a Mac, Go › Go to Folder).
- **FR-039**: Subtasks MUST be pending or done. Add: type in "New subtask" and press Enter (Esc with text only clears the field). Edit: in place, Enter confirms, Esc undoes, empty text is not accepted. Delete: × with an undo option. Complete: moves to the log with the completion date, with an undo option; in the log, the checkbox reopens and the × deletes. "Subtask" is the only name used in the interface.
- **FR-040**: The task log MUST record completed subtasks and week carry-overs.

#### Weekly rollover

- **FR-045**: The week MUST start on Monday at 00:00 in the account's time zone.
- **FR-046**: For each closed week not yet processed, the system MUST keep a snapshot of the tasks, keep tasks at 100% in the original week and move the others to the top of the next week, in the order they were in, preserving identity, progress, importance, notes, subtasks, log and creation date, incrementing the weeks-open counter and recording the carry-over in the log.
- **FR-047**: The rollover MUST be idempotent (including with several devices open), process all weeks in between after an absence and never pull future tasks forward. The person always sees the rollover applied when opening or coming back to the app and, with the app open, within 1 minute after the week changes.
- **FR-048**: Closed weeks MUST show the snapshot in read-only mode, including the notes.

#### Overview and week notes

- **FR-050**: With no task selected, the panel MUST show the overview of the displayed project and week: week notes; pending subtasks of open tasks, in list order, with a checkbox to complete them and a link to the task; and "Worth picking up", with open tasks not updated for 72 hours or more, except in future weeks. No counters, charts or second list of the cards.
- **FR-051**: Changes to title, notes, progress, importance and subtasks count as updates for "Worth picking up"; carry-over in the rollover and reordering do not.
- **FR-052**: Each week and project MUST have a week notes block, with the same editor as the tasks, saved while typing, with no progress, importance or log, outside the card list and not carried over in the rollover. Closed weeks show it read-only; future weeks accept edits. An empty block is treated as non-existent.

#### Saving and connection

- **FR-055**: The footer MUST show the save state: saved, saving, offline (with the number of changes waiting to be sent) or failed.
- **FR-056**: Offline, the content already loaded MUST stay editable, including creating tasks and subtasks; the changes are stored on the device, even if the tab is closed, and are sent in the order they were made when the connection comes back.
- **FR-057**: Offline, opening content not loaded yet MUST show a notice that a connection is needed.
- **FR-058**: Logging out with pending changes MUST require explicit confirmation that they will be discarded. One account's pending changes are never sent on behalf of another.
- **FR-059**: If the session expires with pending changes, the system MUST ask the person to log in again and then send them, without losing text.
- **FR-060**: Changes made on another device MUST show up when coming back to the app or when navigating to another week, project or task.
- **FR-061**: If a title, task notes, week notes or subtask text was changed on another device after this screen loaded it, the system MUST NOT silently overwrite it: it warns whoever saves later and lets them choose which version to keep; the version not chosen stays available to copy until the person closes the notice. Changes to different fields of the same task do not cause a conflict.

#### Appearance in this feature

- **FR-065**: The interface MUST use the Graphite theme in dark mode, the theme font and the Classic gradient. Choosing theme, mode, font and gradient is left to the appearance feature.

### Key Entities *(include if feature involves data)*

- **Account**: the user; unique e-mail, protected password, time zone, creation date. Owns all other data.
- **Session**: an account's access on a device; expires through inactivity or on logout; ended on password reset.
- **Project**: flat grouping with a name, belongs to an account.
- **Task**: belongs to a project and a week; title, notes, important, progress (0–100), position in the group, creation, last update, weeks open, subtasks and log.
- **Subtask**: text, pending or done, creation and completion date.
- **Log entry**: moment, kind (system or note) and text; records subtask completions and carry-overs.
- **Week notes**: rich text of an account for a week + project pair.
- **Weekly snapshot**: read-only copy of a week's tasks at closing time.
- **Rollover state**: last processed week per account, which guarantees idempotency.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new person creates the account and writes the first task in under 1 minute.
- **SC-002**: After logging in, the current week is usable within 2 seconds on a common broadband connection.
- **SC-003**: With a connection, typed text is saved within 3 seconds after the person stops typing.
- **SC-004**: In connection-drop tests from 1 minute to 1 hour, including with the tab closed and reopened on the same device, 100% of the changes made during the outage are saved and visible on another device after reconnecting.
- **SC-005**: Isolation tests covering every operation of the feature record zero accesses to another account's data.
- **SC-006**: In rollover tests with absences of 1, 2 and 5 weeks and with two devices open at the same time, there is no duplicate carry-over and no lost task.
- **SC-007**: The system serves 1,000 people using the app at the same time while keeping SC-002 and SC-003.
- **SC-008**: Every flow of this feature can be completed with the keyboard alone and on a phone with a 360 px wide screen.

## Assumptions

- Login with e-mail and password; e-mail confirmation is not required to start using the app (password recovery handles e-mails signed up by third parties). Sign in with Google and changing the password while logged in are outside this feature.
- There is an e-mail delivery service for password recovery.
- Terms of use and privacy policy (LGPD) start from draft texts written in this feature ([legal/](legal/)), reviewed and adjusted by the product owner before launch, and are shown at sign-up.
- After the account is deleted, system backups that contain its data are discarded within 30 days.
- The account's time zone comes from the sign-up device; changing it is outside this feature.
- New accounts get no sample data.
- The app is always hosted; that is why file links offer "Copy path" instead of opening.
- Sync between devices is not real-time (see FR-060).
- A sequence of specs completes the product: 002 calendar and due dates (includes "On the agenda" in the overview and the due date on cards), 003 search (Ctrl+Space), 004 appearance (themes, mode, font, gradient, panel in the profile) and 005 prototype import and backup (export/import JSON, Files menu).
- These stay outside the product, as in the prototype: collaboration and sharing, integrations, notifications, subprojects, kanban, urgency levels, automatic progress, changing the week after creation, dragging tasks between weeks or projects, renaming or deleting projects, attachments, AI, time tracking and trash.
