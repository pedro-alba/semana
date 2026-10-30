<!--
Sync Impact Report
- Version: 1.0.0 → 1.1.0
- Changed: the constitution was translated to English; "Product constraints" now says the UI is in
  English by default, with a Brazilian Portuguese translation (it used to say Brazilian Portuguese only)
- Principles: I Fewer controls, more text; II The week is the unit; III Nothing is lost;
  IV Each account's data is its own; V Simplicity; VI Tests where the rule is subtle
- Sections added: none
- Sections removed: none
- Templates: plan-template.md reads this constitution in the "Constitution Check"; no change needed
- TODOs: none
-->
# Semana Constitution

## Core Principles

### I. Fewer controls, more text

Every interface element MUST earn the space it takes by helping to write, decide or pick up
where one left off. Semana MUST NOT gain professional management features (urgency levels,
kanban, time tracking, metrics dashboards). Features for occasional use stay off screen,
reachable by shortcut. No modals: the task opens in the content panel.

Rationale: the product replaces a text document; every extra control pulls it away from that.

### II. The week is the unit

The week (Monday to Sunday) is the planning unit. The current week is the focus; past and
planning weeks are secondary. Closed weeks are read-only. The weekly rollover MUST be
idempotent and process every pending week after an absence.

### III. Nothing is lost

No user data is lost without confirmation or a way to undo. Text MUST be saved while typing.
Save failures and lack of connection MUST be visible, and changes made during an outage MUST be
sent when the connection is back. Imports validate before replacing anything.

### IV. Each account's data is its own

Each account sees and changes only its own data. All data access MUST be restricted to the
account authenticated on the server, and this isolation MUST have automated tests. Rich content
MUST be sanitized on save and on display; links accept only http, https, mailto and file.
Passwords are never stored in readable form.

Rationale: Semana holds personal notes; a leak between accounts is the worst possible failure.

### V. Simplicity

The smallest solution that meets the spec wins. A new dependency, layer or service MUST be
justified in the plan (complexity table) with the simpler alternative that was rejected.
Nothing is built "for later".

### VI. Tests where the rule is subtle

Rules with edge cases MUST have automated tests: weekly rollover, event recurrence, search
(accents, ranking), HTML sanitizing, link and path conversion, isolation between accounts and
sending changes after an outage. A simple interface does not require per-component tests.

## Product constraints

- Interface in English by default, with a Brazilian Portuguese translation picked from the
  browser language or the account setting.
- Web application; desktop and phone are first-class (list and content stack on smaller
  screens; touch gestures equivalent to mouse ones).
- Accessibility: everything keyboard-operable; minimum 4.5:1 contrast for text; progress
  available to screen readers.
- Appearance belongs to the user: theme, mode, font and gradient do not change data.

## Development workflow

- Every feature goes through `/speckit-specify` → `/speckit-clarify` (when there is ambiguity) →
  `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`.
- The prototype (`specs/semana.html`) and its v2.6 specification (`specs/spec.md`) are the
  behavior reference. Divergences MUST be explicit in the feature spec.
- A feature is only done when its acceptance criteria are verified.

## Governance

This constitution takes precedence over other project practices. Amendments are made by editing
this file, with an impact report and semantic versioning: MAJOR to remove or redefine a
principle, MINOR to add a principle or section, PATCH for wording. Every plan MUST pass the
"Constitution Check"; violations require justification in the complexity table.

**Version**: 1.1.0 | **Ratified**: 2026-10-27 | **Last Amended**: 2026-10-29
