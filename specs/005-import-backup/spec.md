# Feature Specification: Prototype import and backup

**Feature Branch**: `005-import-backup`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "Feature 005: prototype import and backup. Bring from the prototype (specs/spec.md v2.6, Data and persistence; specs/semana.html, Files menu, migrate, normalize, validateState) into the multi-user app: each person exports their own account's data to a JSON file and imports a backup from the app or from the prototype (v1 and v2) into their own account. User decision: importing replaces everything in the account, after validating the file and an explicit confirmation. The server backup (the whole database) is left for deployment."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bring the prototype into the account (Priority: P1)

Someone who already used the local prototype exports its backup and imports it into the new account. They pick up where they left off without retyping anything.

**Why this priority**: it is the bridge between the prototype and the app. Without it, people who already use Semana would lose their history when they move.

**Independent Test**: export a prototype backup with tasks in several weeks, subtasks, formatted notes, week notes, recurring events, due dates and snapshots; import it into a new account; check everything in the app.

**Acceptance Scenarios**:

1. **Given** a logged-in account, **When** the person opens the Files menu (now the BACKUP section of the profile menu), **Then** they see "Export full backup", "Import and replace" and the explanation of what the backup includes.
2. **Given** a v2 prototype backup, **When** the person picks it in "Import and replace", **Then** the app validates the file and shows a confirmation with what will be imported (number of projects, tasks, events and weeks) and the warning that the account's current data will be deleted.
3. **Given** the confirmation, **When** the person confirms, **Then** the account has exactly the file's projects, tasks (with subtasks, log, due date, importance, progress and order), week notes, events and snapshots, and the app opens on the current week with the message "Backup imported."
4. **Given** a v1 prototype backup, **When** the person imports it, **Then** it is converted as in the prototype (description into paragraphs, high urgency becomes important, actions become subtasks, reports become log entries, links become links in the notes).
5. **Given** the open confirmation, **When** the person cancels, **Then** nothing changes.
6. **Given** a backup whose processed week is before the current week, **When** it is imported, **Then** the weekly rollover runs as usual (pending tasks move to the current week and closed weeks get a snapshot).

---

### User Story 2 - Keep a copy of your own data (Priority: P1)

The person downloads a file with everything they wrote, to keep wherever they want or to restore later.

**Why this priority**: the data belongs to the person (LGPD, portability), and the backup is the safety net against their own mistakes.

**Independent Test**: export, delete and change things in the account, import the exported file and check that the account is back to the exported state.

**Acceptance Scenarios**:

1. **Given** an account with data, **When** the person picks "Export full backup", **Then** the browser downloads `semana-backup-YYYY-MM-DD.json` with projects, tasks, subtasks, log, week notes, events and snapshots for every week.
2. **Given** a file exported by the app, **When** it is imported into the same or another account, **Then** the account's content is the same as at export time (lossless round trip).
3. **Given** changes not yet sent from this device, **When** the person exports, **Then** they are sent first, so they end up in the file; with no connection, the export warns that it needs a connection.

---

### User Story 3 - An invalid file breaks nothing (Priority: P2)

A wrong, corrupted, oversized or foreign file is rejected without touching the current data.

**Why this priority**: "nothing is lost" (constitution III). Replacing everything requires validation to come first.

**Independent Test**: import broken JSON, JSON in another format, a file over the limit and a backup with dangerous HTML in the notes; check the messages and that data is intact.

**Acceptance Scenarios**:

1. **Given** a file that is not a valid backup, **When** the person picks it, **Then** "Invalid backup. Your current data was kept." appears and nothing changes, with no confirmation asked.
2. **Given** a file over 50 MB, **When** the person picks it, **Then** it is rejected with the same message.
3. **Given** a backup with scripts, styles or disallowed links in the notes, **When** it is imported, **Then** the content is sanitized like any other text in the app (FR-035 of 001).
4. **Given** a failure in the middle of writing, **When** the import does not finish, **Then** the account stays exactly as before (all or nothing).

---

### Edge Cases

- Importing with no connection: the menu warns that importing needs a connection and does not open the file picker.
- Pending changes on this device when importing: they are discarded, and the confirmation says how many.
- Another device on the same account open during the import: when it returns to the tab, it loads the new data. Its pending changes to items that no longer exist are discarded without a conflict, as with a deletion made on another device.
- Prototype backup with sample data (`demo`): imported like any other. There is no "Start without examples" in the app.
- Projects: the file's projects replace the account's, including Personal and Work. A file with no projects is invalid.
- File IDs that already exist in another account: the import must not fail or touch the other account. Items get new IDs when needed, keeping their links (task → project, subtask → task).
- Event linked to a project that is not in the file: it ends up with no project.
- Snapshots of future weeks or with a strange format: ignored.
- Text fields over the app's limits (title, subtask, notes): the file is rejected as invalid, without truncating.
- Exporting an empty account: downloads a valid backup with only the projects.
- Appearance: not part of the backup (as in the prototype) and does not change on import.

## Requirements *(mandatory)*

### Functional Requirements

#### Files menu

- **FR-001**: The profile menu MUST have the BACKUP section (revised on 2026-10-29: in the prototype it was a separate Files menu in the header), with "Export full backup", "Import and replace" and the text "The backup includes tasks, subtasks, notes, events and weekly snapshots." ("Download this prototype" and "Start without examples" are left out).
- **FR-002**: The menu MUST be keyboard-operable and fit in 360 px.

#### Export

- **FR-010**: Export MUST download a JSON file in the app's own format, with a format and version marker, holding all the account's data: projects, tasks (with subtasks, log, due date, order, progress, importance, creation, last activity and weeks carried over), non-empty week notes, events and snapshots.
- **FR-011**: The file name MUST be `semana-backup-YYYY-MM-DD.json`, with today's date in the account's time zone.
- **FR-012**: Before exporting, pending changes from this device MUST be sent. With no connection, the export does not happen and the app says "No connection. Connect to export."
- **FR-013**: The export MUST contain only data from the logged-in account.

#### Import

- **FR-020**: Import MUST accept files exported by the app and v1 and v2 prototype backups. Prototype files are converted as the prototype does (v1 → v2, specs/spec.md v2.6, filling in missing fields) and then to the app's format.
- **FR-021**: The file MUST be fully validated before any change. An invalid file or one over 50 MB shows "Invalid backup. Your current data was kept." and changes nothing.
- **FR-022**: A valid file MUST open a confirmation inside the menu itself (no modal) with a summary of the content, the warning "This deletes all of the account's current data and replaces it with the file's." and, if any, how many pending changes from this device will be discarded.
- **FR-023**: Once confirmed, the import MUST replace at once all of the account's projects, tasks, subtasks, log, week notes, events and snapshots. If it fails, nothing changes.
- **FR-024**: All imported rich text MUST go through the app's usual sanitizing.
- **FR-025**: After importing, the weekly rollover MUST run from the file's processed week, and the app MUST open the current week's overview in the first project with "Backup imported."
- **FR-026**: Import MUST need a connection. Without one, the app says "No connection. Connect to import."
- **FR-027**: The import MUST write only to the logged-in account and never change another account, even with repeated IDs.

### Key Entities *(include if feature involves data)*

- **App backup**: JSON file with a format and version marker, projects, tasks (with subtasks and log), events, week notes, snapshots and the processed week.
- **Prototype backup**: the prototype's state file (v1 or v2), accepted only as input.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Exporting and importing back leaves the account 100% the same (projects, tasks, subtasks, log, notes, events, snapshots).
- **SC-002**: A real prototype backup with 2 years of use (about 1,500 tasks and 200 note blocks) imports in under 30 seconds on a common broadband connection.
- **SC-003**: In tests with invalid files (broken JSON, unknown format, over the limit, text over the limits, failure in the middle of writing), 100% leave the account as it was.
- **SC-004**: Isolation tests record zero changes to another account when importing, including with IDs repeated across accounts.

## Assumptions

- The exported backup uses the app's own format, close to the data stored on the server (the owner allowed not following the prototype's format, 2026-10-29). It does not open in the prototype; the prototype becomes only an import source.
- Importing replaces everything, after validation and confirmation (owner's decision, 2026-10-29). The prototype replaced without asking; the confirmation is the difference.
- Appearance stays out of the backup, as in the prototype. It is already stored in the account (feature 004).
- The server backup (periodic copies of the whole database, for the administrator) is left for deployment and is not part of this feature.
- Export and import need a connection: with data on the server, a file built only from the device cache could come out incomplete.
- The 50 MB limit comes from the prototype.
