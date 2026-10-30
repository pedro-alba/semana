# Semana — MVP specification

Version 2.6 · October 23, 2026

The prototype (`specs/semana.html`) originally had a Portuguese interface; it was later translated to English. Interface text in this document is given in English, as in the app.

## Goal

A personal app for day-to-day notes organized by week. It replaces a text document full of highlights with tasks that have their own notes, free-form week notes, subtasks, optional due dates, search and a simple calendar. Use is individual; the product avoids professional management features and any element that does not help to write, decide or pick up where one left off.

The MVP runs in a browser, with local data, no account, backend or sync.

## Principles

- Fewer controls, more text. Every interface element must earn the space it takes.
- The week is the planning unit. The current week is the focus; past and planning weeks are secondary.
- Nothing is lost without confirmation or a way to undo.
- Features for occasional use stay off screen: search opens by shortcut and is the only layer over the interface.
- Appearance belongs to the user: theme, mode, font and progress colors are personal choices and do not change data.

## Structure

- Projects are flat groupings. Personal and Work come first; others can be created with the + button next to the selector.
- On desktop, the task list takes about 25% of the width and the content the rest. No modals. On smaller screens, list and content stack.
- On desktop, the board fits the window height; list and content scroll internally.
- The app takes the full available width.
- The header has the brand, the Tasks/Calendar navigation, a discreet hint of the search shortcut, the Files menu and the profile icon, which opens the appearance panel. There is no account flow.
- The footer shows the save state and the phrase "One day at a time."

## Appearance

Four independent choices in the profile icon's panel, applied right away, without reloading and without losing the open task or the text being edited.

### Theme

Sets shape, interface typography and the overview layout.

| Theme | Style | Cards | Overview |
| --- | --- | --- | --- |
| Graphite (default) | Neutral, system typography | Surface with a side stripe and a tint in the progress color | Week notes as the main column; subtasks, agenda and "Worth picking up" on the right |
| Paper | Warm and editorial, serif titles and notes, dividers instead of boxes, the content like a sheet | Numbered index cards, filled with the progress color | Week notes next to subtasks and "Worth picking up"; agenda as a bottom strip |
| Ink | High contrast, firm lines, no rounded corners, a single signal red | Filled with the progress color, firm border, offset shadow when selected | Week notes in a top strip; three equal columns below |

### Mode

Light, Dark or System (follows the operating system preference and tracks changes). Each theme has both versions. On first open, the mode is the theme's natural one: dark in Graphite, light in Paper and Ink.

### Task font

Theme (default), Roboto Mono, Sans serif or Serif. The font applies to content written by the user: task title, subtasks, task and week notes, and card titles. The interface (menus, buttons, calendar, dates) keeps the theme's font, so numbers and controls stay readable and each theme keeps its identity. Roboto Mono is embedded in the file (SIL Open Font License 1.1) and works offline; the others use system fonts. Monospaced fonts are shown slightly smaller to keep the same reading width.

### Progress gradient

| Gradient | 0% | 50% | 100% |
| --- | --- | --- | --- |
| Classic (default) | RGB(244,247,251) | RGB(123,184,247) | RGB(124,216,173) |
| Sunset | RGB(250,243,232) | RGB(248,198,140) | RGB(242,162,170) |
| Lavender | RGB(246,244,252) | RGB(202,190,250) | RGB(238,172,214) |
| Moss | RGB(245,246,236) | RGB(214,228,150) | RGB(138,208,156) |
| Traffic light | RGB(247,190,180) | RGB(248,224,140) | RGB(140,214,166) |
| Neutral | RGB(246,246,246) | RGB(208,211,216) | RGB(172,177,186) |

Linear interpolation between stops. All stops keep at least 4.5:1 contrast with the card text. The gradient applies to cards, the list legend, the open task marker and due dates in the calendar.

### Persistence

The four choices live in the browser's local storage (key semana-prefs), separate from the data and outside the backup, and are applied before the page's first paint.

## Weekly navigation

- Four controls of the same size: previous week, next week, pick a week (calendar icon) and back to the current week (circular arrow).
- Back to the current week also closes the open task and shows the overview. In the calendar, it only goes back to the current week. The "semana." brand leads to the current week's overview from any screen.
- Close the task and go back to the overview of the displayed week: × button on the task bar, Esc (when no menu, form, link bubble or search is open) or clicking the open card again. Focus returns to the card. Esc in the "New subtask" field with text only clears the field.
- The current week gets no label. Past weeks show PAST; future ones, PLANNING.
- Changing project or week goes back to the overview.

## Task list

- Clickable cards, with no decorative arrows. The color shows progress; there is no visible percentage, number or bar. The percentage is available to screen readers.
- The card shows the title, the due date (if any), the number of pending subtasks and, if the task came from earlier weeks, how many weeks it has been open (e.g. "↪ 2nd week"). Important tasks show a red flag.
- The order is the user's. Open tasks sit above "Done"; within each group, the position set by dragging applies. Flag and due date do not reposition cards.
- The gradient legend sits at the bottom of the column, outside the scrolling area, with the gesture hint. With a task selected, a marker shows its position on the gradient.

## Reordering

- Mouse: drag the card up or down.
- Touch: hold the card for about 0.35 s and drag. Swiping without holding still scrolls the list.
- Keyboard: Alt + up or down arrow on the focused card.
- The card follows the pointer and the others make room. Near the edges, the list scrolls by itself.
- Only within the same group (open or done). Past weeks cannot be reordered.
- A new task goes at the end of the open ones. When done, the task goes to the end of Done; when reopened, to the end of the open ones. On rollover, carried-over tasks go to the top of the next week, in the order they were in.
- Reordering does not count as an update for "Worth picking up".

## Progress

- Set by dragging the selected card horizontally. The movement is relative to where the gesture started and only takes effect after a few pixels; a simple tap does not change progress.
- By keyboard, with the selected card focused, the left and right arrows adjust by 5% (with Shift, 10%).
- Reaching 100% moves the task to Done; lowering it returns it to the open ones. Completing subtasks does not change progress, and 100% does not complete subtasks.

## Importance

A single binary signal: important or not. Toggled by the flag on the task bar. There are no urgency levels, and neither the weekly rollover nor the due date marks tasks as important.

## Due dates

- Optional: one date per task, with no time. Set with the "Due date" button on the line below the title; the × removes it.
- The due date is independent of the week. The week says when the task is being worked on; the due date says when it has to be ready. The rollover moves the task and keeps the due date.
- On the card: "due today", "due tomorrow", "due Fri" (same week) or "due Nov 03"; if it passed and the task is open, "was due Oct 20" in red. Done tasks show no due date on the card.
- In the calendar: a "Due dates" strip above "All day", shown when the week has due dates. Each due date shows the progress color and the title and opens the task on click, going to its week and project. It respects the project filter. Overdue ones show in red; those of done tasks, struck through.
- In the overview, "On the agenda" shows the week's due dates of open tasks, from all projects, before the events of the same day. In the current week, due dates missed in earlier weeks show at the top as overdue.
- Setting, changing or removing the due date counts as a task update.

## Creating tasks

- "+ New task" creates the task right away in the selected project and the displayed week, at 0%, and opens the document with the title focused. In a past week, the task goes to the current week.
- To plan a future week, navigate to it and create the task there. The week does not change after creation.
- A task left completely blank (no title, notes, subtasks, progress, importance or due date) is discarded when leaving it.

## Task screen

The open task is a single document that takes the whole content panel. Title, subtasks, notes and log sit on the same card, in a centered reading column. Clicking empty space on the card puts the cursor in the notes.

1. Fixed bar at the top: bold, italic, size (Heading, Subheading, Text), highlight, list and link; on the right, importance flag, trash and × to go back to the overview. With a mouse, the formatting buttons only show with the pointer over the task or while editing, as in week notes; on touch screens they are always visible; flag, trash and × are always visible. In closed weeks, the bar shows the read-only notice and the ×.
2. Large title, editable in place. Enter goes to the notes.
3. Discreet line with the progress color, project, week, weeks open (if any) and due date.
4. Pending subtasks, followed by the "New subtask" field.
5. Notes in rich text.
6. Log, when there is one: completed subtasks and carry-overs.

Shortcuts: Ctrl/Cmd+B bold, Ctrl/Cmd+I italic, Ctrl/Cmd+Shift+H highlight, Ctrl/Cmd+Shift+8 list, Ctrl/Cmd+K link, Ctrl/Cmd+Alt+1, 2 and 0 for Heading, Subheading and Text.

Title and notes save while typing. When switching tasks or screens, or when hiding the tab, pending changes are written right away.

The trash asks for confirmation on the bar itself before deleting. Deleting keeps the snapshots of closed weeks.

## Notes

- Formatting limited to bold, italic, three sizes (Heading, Subheading, Text), highlight, bulleted list and links.
- Pasting from other editors, such as Google Docs, keeps bold, italic, headings, lists, highlights and links and drops the rest (fonts, colors, arbitrary sizes, images).
- Content is stored as HTML restricted to p, h2, h3, ul, ol, li, strong, em, mark, a and br. Links accept only http, https, mailto and file. All HTML is sanitized on save, import and display.
- The highlight is stored without a color; the displayed color comes from the theme and mode.

## Links

- The Link button (Ctrl/Cmd+K) opens a form with "Address or file path" and "Display text". With text selected, the link applies to the selection.
- It accepts web addresses (with or without https://, e.g. site.com.br), e-mail and file paths on the computer: Windows (C:\Folder\file.pdf, including in quotes, as "Copy as path" outputs it), network (\\server\folder\file) and macOS/Linux (/Users/name/file.pdf). Paths are stored as file:// addresses. Paths with ~ ask for the full path.
- With no display text, the link shows the shortened address or the file name.
- Pasting an address or path on its own creates the link automatically; with text selected, it turns the selection into a link.
- With the cursor on a link, a bubble shows the target and the actions Open, Edit and Remove (and Copy path, for files). Ctrl/Cmd+click opens directly. When reading closed weeks, one click opens.
- Local files: browsers only open file:// addresses when Semana is open as a local file. On a hosted page, Open gives way to Copy path, and the notice explains where to paste it (File Explorer; on a Mac, Go › Go to Folder). File links have a dotted underline and a document icon.
- In an event, the "Location or link" field gets a button to open it when it holds an address or path.

## Subtasks and log

- "Subtask" is the only name for checklist items across the interface.
- A subtask is pending or done. There are no other states.
- Add: type in "New subtask" and press Enter.
- Edit: click the text and change it; Enter confirms, Esc undoes. Empty text is not accepted. Long texts wrap.
- Delete: the item's × button, with an undo option.
- Complete: the checkbox moves the subtask to the log, with a completion date and an undo option. In the log, the checkbox reopens the subtask and the × deletes it.
- The log also records week carry-overs.

## Weekly rollover

When the app loads, when returning to the tab and every minute while open:

1. Compute the current week (Monday, 00:00, browser time zone).
2. For each closed week not yet processed, store a snapshot of the tasks.
3. Keep tasks at 100% in their original week.
4. Move the others to the next week, keeping ID, progress, importance, due date, notes, subtasks and creation, and put them at the top of the list, in the order they were in.
5. Increment the week counter and record the carry-over in the log.
6. Update the processed week and persist.

Running again in the same week does not duplicate carry-overs. After an absence, all the weeks in between are processed. Future tasks are never pulled forward. With the app closed, the rollover is applied on the next open.

Closed weeks show the snapshot in read-only mode.

## Overview

Shows when the app opens and whenever no task is selected. Week notes, subtasks and "Worth picking up" respect project and week; the agenda shows all projects.

- Week notes (see below).
- Pending subtasks of open tasks, in list order, with a checkbox to complete them right there and access to the task.
- On the agenda: the week's due dates and events with day, time (or "due"), project and access. Times at 14px.
- Worth picking up: open tasks with no update for 72 hours or more (except future weeks).

No intro header, progress counters, charts or second list of the cards.

Updates that count for "Worth picking up": title, notes, progress, importance, due date and subtasks. Automatic carry-over and reordering do not reset the counter.

## Week notes

- A free text block in the overview, one per week and project, for what is not a task: ideas, messages, phone numbers, loose reminders.
- Same editor as task notes: formatting, shortcuts, links and pasting. The formatting bar shows on hover or while editing.
- Saves while typing. It has no progress, due date, importance or log, does not show in the card list and is not carried over on rollover: it stays in the week it was written in.
- Closed weeks show the notes in read-only mode; future weeks can get planning notes.
- Included in search and backup. An empty block is not stored.

## Search

- Ctrl+Space opens a box in the middle of the screen, over the interface, from any screen. Ctrl+Space again, Esc or a click outside closes it and returns focus to where it was.
- With no text typed, the list shows the most recently updated open tasks.
- As you type, the list shows up to ten results among tasks (title, subtasks and notes) and week notes, from every week and project. It ignores case and accents ("reuniao" finds "Reunião"). With more than one word, all of them must appear.
- Order: title before content; start of the title before the middle; then the current week, future weeks and the most recent ones. Done tasks sit below open ones with the same score.
- Each result shows the progress color (or the notes icon), the title, project, week and status (due date or done) and, when the term is in the content, a snippet with the terms highlighted.
- The first result comes highlighted: Enter opens it, and with a single result Enter is enough. Up and down arrows move the highlight; clicking also opens.
- Opening goes to the result's week and project, opens the task (or the overview, for week notes) and selects the first occurrence of the term in the notes.
- There is no search button. A secondary text in the header ("Search Ctrl Space") shows the shortcut; it goes away on touch screens and on phones, where search has no entry point yet.

## Calendar

- Weekly grid from Monday to Sunday, from 00:00 to 24:00, initially scrolled to 07:00, with a due date strip (when there are any) and an all-day strip. Header "Agenda". On desktop, the page fits the window; only the grid and, if needed, the editor scroll.
- Starts with all projects and offers a filter, which applies to events and due dates.
- Event: title, start, end, all day, optional project, location or link, description and recurrence. Events are not linked to tasks; due dates belong to tasks.
- End after start; maximum duration of 31 days. For all day, the interface takes the inclusive last day and the model uses an exclusive end.
- "Repeat until" turns on the recurrence when filled in and only then shows "Frequency" (weekly by default, or monthly). Clearing the date turns the recurrence off. The end date is inclusive.
- Weekly keeps the weekday and time; monthly keeps the day of the month, and months without that day produce no occurrence.
- Editing and deleting affect the whole series. Create with the button or by clicking a time slot. Side editor on desktop, stacked on smaller screens. Overlaps are spread into columns.

## Data and persistence

| Entity | Fields |
| --- | --- |
| Project | id, name |
| Task | id, projectId, week, title, description (restricted HTML), important, due (date or empty), order, progress, createdAt, lastActivity, carries, subtasks, log |
| Subtask | id, text, done, createdAt, doneAt |
| Log entry | id, at, kind (system or note), text |
| Event | id, title, start, end, allDay, projectId, repeat, until, description, location |
| Weekly snapshot | week → copy of the tasks at closing |
| Week notes | "week\|project" → restricted HTML |
| State | version (2), processed week, projects, tasks, events, notes, snapshots |
| Preferences | theme, mode, font, palette (local storage, outside the backup) |

- A single HTML/CSS/JavaScript file, with no dependencies or external calls.
- Local IndexedDB. The v2 state is stored apart from v1; existing v1 data is converted on first open and the original stays stored.
- Fields added after 2.0 are filled in on open or import: empty due date, order derived from the previous rule (important first, then creation) and empty week notes.
- Without IndexedDB, the session uses memory and warns to export a backup. Save failures show in the footer.
- Full JSON backup, including snapshots. Import accepts v1 and v2 backups, validates before replacing and keeps the current state if the file is invalid.
- v1 conversion: text description becomes paragraphs; high urgency becomes important; pending or waiting actions become pending subtasks and completed actions become done subtasks; reports become log entries; links become links in the notes. Attachments and links between events and tasks are not imported.
- "Download this prototype" produces the app's clean HTML, with starter samples, without the session data and without scripts injected by the page hosting it.
- This specification does not ship with the app file and cannot be downloaded from it; it is kept separately, with the project.
- Weekly dates and due dates are civil dates (YYYY-MM-DD); event times are local; activity uses ISO instants.

## Acceptance criteria

1. First open: Personal, current week, overview, dark Graphite theme.
2. A new project shows as an independent grouping.
3. A task created in a future week does not show in the current week.
4. The task opens in the content panel as a single document, with no modal.
5. Dragging the selected card sideways changes the color; a simple tap does not; 100% moves it to Done.
6. Dragging a card up or down changes its position, which persists after reload; on touch, only after holding; by keyboard, with Alt and arrows.
7. Bold, italic, sizes, highlight, list and links work and persist after reload.
8. Pasting from Google Docs keeps highlights and links and drops unsupported styles.
9. Notes are saved while typing.
10. Subtasks can be created, edited, completed, reopened and deleted; deleting and completing can be undone.
11. Deleting a task requires confirmation.
12. Back to the current week closes the task and shows the overview; ×, Esc and clicking the open card again go back to the displayed week's overview, without changing progress.
13. The rollover keeps data and due dates, increments the weeks open, keeps done tasks and is idempotent, including after several weeks.
14. The overview shows week notes, pending subtasks, agenda with due dates, and stalled tasks, without duplicating the card list.
15. The due date shows on the card, in the agenda and in the calendar's due date strip, which opens the task; when overdue, it shows as late.
16. Links to sites open in a new tab; file paths become file:// links, which open when the app is a local file and, on a hosted page, copy the path.
17. The calendar lets you create, edit, delete and filter events, with weekly and monthly recurrence respecting limits and short months.
18. Theme, mode, font and gradient change right away, do not change data, the open task or text being edited, and survive a page reload.
19. The backup exports and imports (v1 and v2) with validation; persistence failures are explicit.
20. Week notes save while typing, stay in the week they were written in and are read-only in past weeks.
21. Ctrl+Space opens search; typing filters ignoring accents; Enter opens the highlighted result, goes to the right week and selects the term found.

## Out of the MVP

Accounts, sync, collaboration, integrations, notifications with the app closed, subprojects, kanban, urgency levels, automatic progress, time on due dates, due dates that move the task's week, changing the week after creation, dragging tasks between weeks or projects, renaming or deleting projects, attachments, links between events and tasks, AI, time tracking, trash bin, individual recurrence exceptions, theme and palette editor, and user-uploaded fonts.

The artifact is a working prototype with demo data and local persistence; it does not guarantee behavior in every browser.
