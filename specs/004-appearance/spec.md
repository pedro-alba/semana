# Feature Specification: Appearance

**Feature Branch**: `004-appearance`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "Feature 004: appearance. Bring from the prototype (specs/spec.md v2.6, Appearance section; specs/semana.html, THEMES/MODES/FONTS/PALETTES, prefsHTML, setPref, applyMode) to the multi-user app: a panel on the profile icon with four independent choices (theme Graphite/Paper/Ink, mode Light/Dark/System, task font, progress gradient), applied right away without reloading and without losing the open task or the text being edited. User decision: the preferences live in the account (they apply on every device), with a copy in the browser so the app opens in the right appearance and works offline. The panel sits alongside the account options already in the profile menu (log out, delete account). Appearance does not change task data."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Choose the appearance (Priority: P1)

The person opens the profile menu and picks theme, mode, task font and progress gradient. Each choice changes the interface right away, without reloading and without losing what is open.

**Why this priority**: it is the feature. Today the app only has dark Graphite, the theme font and the Classic gradient.

**Independent Test**: with a task open and text being edited in the notes, change each of the four choices and check that the interface changes, the task stays open, the text and cursor stay where they were and no data changes.

**Acceptance Scenarios**:

1. **Given** the profile menu is open, **When** the person looks at the menu, **Then** they see the account's e-mail, the sections THEME, MODE, TASK FONT and PROGRESS GRADIENT, with the current choice marked in each, and the actions Log out and Delete account.
2. **Given** the Graphite theme, **When** the person picks Paper, **Then** the interface takes on Paper's wording, cards and overview layout, without reloading.
3. **Given** System mode, **When** the operating system switches between light and dark, **Then** the app follows without reloading.
4. **Given** the Roboto Mono font, **When** the person looks at the screen, **Then** titles, subtasks, notes and card titles use Roboto Mono, and menus, buttons, calendar and dates keep the theme font.
5. **Given** the Sunset gradient, **When** the person looks at the list, **Then** cards, legend, open-task marker and due dates in the calendar use the Sunset gradient.
6. **Given** an open task with the cursor in the middle of the notes, **When** the person changes any of the four choices, **Then** the task stays open, the text does not change and the cursor stays where it was.

---

### User Story 2 - The same appearance on every device (Priority: P2)

The person picks the appearance on the computer and, when signing in on the phone, finds the same appearance without choosing again.

**Why this priority**: it is the owner's decision for the multi-user app; without it, each device would have its own appearance, as in the prototype.

**Independent Test**: pick Ink, Light mode, Serif and Moss in one browser; sign in to the same account in another browser and check the four choices; reload offline and check that the appearance shows without flashing the default one.

**Acceptance Scenarios**:

1. **Given** choices made on one device, **When** the person signs in on another device, **Then** the interface already opens with those choices.
2. **Given** both devices with the app open, **When** the person changes the appearance on one of them, **Then** the other uses the new appearance when the app is opened, reloaded or becomes visible again, as happens with content.
3. **Given** the app was opened before on this device, **When** the person reopens it, online or offline, **Then** the page's first paint already uses the chosen appearance, without showing the default first.
4. **Given** the connection is lost, **When** the person changes the appearance, **Then** the change applies right away on this device and reaches the account when the connection comes back, like other changes.

---

### Edge Cases

- Account that never chose: Graphite, Dark mode, Theme default font, Classic gradient (the app's current appearance).
- Choices made on two devices while offline: the last one to reach the server wins; there is no conflict warning (appearance is not content).
- Another account signs in on the same browser: the appearance becomes that account's as soon as sign-in finishes.
- Sign-in, sign-up, password recovery, terms and privacy screens: use the last appearance saved in this browser, or the default if there is none.
- System mode with the system preference changing while the app is open: follows right away.
- Profile menu on a 360 px screen: the whole menu (appearance and account) is reachable, scrolling inside it if it does not fit, with no sideways scrolling of the page.
- Unknown value coming from another app version: ignored; the default applies for that choice.
- Log out or Delete account confirmation open in the menu: the appearance disappears from the menu until the confirmation is completed or cancelled.

## Requirements *(mandatory)*

### Functional Requirements

#### Choices

- **FR-001**: The profile menu MUST offer four independent choices, as in the prototype: theme (Graphite, Paper, Ink, with a sample and a description), mode (Light, Dark, System), task font (Theme default, Roboto Mono, Sans serif, Serif) and progress gradient (Classic, Sunset, Lavender, Moss, Traffic light, Neutral). Theme, mode, font and gradient follow the definitions in the Appearance section of `specs/spec.md` (v2.6).
- **FR-002**: Each choice MUST apply right away, without reloading the page and without closing the open task, losing text being edited or moving the cursor.
- **FR-003**: System mode MUST follow the operating system's preference and track changes while the app is open.
- **FR-004**: The chosen font MUST apply only to content written by the person (task and card titles, subtasks, task notes and week notes); the interface keeps the theme font. Roboto Mono works without internet.
- **FR-005**: The chosen gradient MUST apply to cards, the list legend, the open-task marker and due dates in the calendar.
- **FR-006**: Each group of choices MUST be usable by keyboard and announced to screen readers as an option group with the current choice marked.
- **FR-007**: The profile menu MUST keep the account's e-mail and the Log out and Delete account actions; while a Log out or Delete account confirmation is open, the menu shows only the confirmation.

#### Saving and syncing

- **FR-010**: The choices MUST be saved in the account and apply on every device the person signs in on.
- **FR-011**: Each browser MUST keep a copy of the last appearance, applied before the first paint of any app page, offline included.
- **FR-012**: A choice made offline MUST apply right away and be sent to the account when the connection returns, the same way as other changes; between concurrent choices, the last one received wins.
- **FR-013**: On sign-in, the account's appearance MUST replace the browser's copy.
- **FR-014**: Appearance MUST NOT change tasks, notes, events or any other data, and the text "Preferences for your account. Your data doesn't change." shows in the panel.
- **FR-015**: Only the account itself MUST be able to read or change its appearance.

### Key Entities *(include if feature involves data)*

- **Appearance**: four choices (theme, mode, font, gradient) tied to an account; one per account, with a copy in each browser where the account signed in.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each change of choice shows on screen within 100 ms, without reloading, in 100% of the theme, mode, font and gradient combinations (3 × 3 × 4 × 6).
- **SC-002**: In every theme and mode combination, card text keeps a contrast of at least 4.5:1 against every stop of the six gradients.
- **SC-003**: When signing in on a second device, 100% of the four choices match the first device's.
- **SC-004**: When reopening the app on this device, online or offline, the default appearance is not shown even for an instant when another one was chosen.
- **SC-005**: Changing the appearance with an open task and text being edited changes no data, does not close the task and keeps the cursor, in 100% of tests.
- **SC-006**: The profile menu is usable with the keyboard only on desktop and with touch only on a 360 px phone.

## Assumptions

- The reference behavior is the prototype's (specs/spec.md v2.6, Appearance section; specs/semana.html). Differences: the choices live in the account, not only in the browser (owner's decision, 2026-10-28), and the panel text says "Preferences for your account" instead of "Preferences for this browser".
- The styles for the three themes, the modes, the fonts and the six gradients already exist in the app since feature 001 (copied from the prototype); this feature wires them to the choices.
- On first open, the prototype uses the theme's natural mode (dark for Graphite, light for Paper and Ink). Here, a new account starts in dark Graphite, which is Graphite's natural mode; changing the theme does not change the chosen mode.
- A change made on another device shows when opening, reloading or returning to the app's tab, like content (feature 001); live updates with the tab in the foreground are out of scope.
- Appearance goes into the feature 005 backup if that feature decides so; this feature does not deal with export.
- On log out, the browser's copy stays (it is only appearance); on account deletion, it is erased along with the other local data.
