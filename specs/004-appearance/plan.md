# Implementation Plan: Appearance

**Branch**: `004-appearance` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-appearance/spec.md`

## Summary

Wire the theme, mode, font and gradient styles, which have been in `app.css` since 001, to the prototype's panel in the profile menu, and save the choices in the account.

- **Server**: an `account.appearance` column (JSON), the `account.appearance` operation in the usual queue and the `appearance` field in the responses that already return the account.
- **Client**: a small classic script, `appearance.js`, loaded in the `<head>` of every page. It applies the browser copy before the first paint ([R1](research.md)), and the prototype's panel comes back to the profile menu.

## Technical Context

**Language/Version**: Python 3.12; JavaScript ES2022 with no build (same as 001)

**Primary Dependencies**: none new

**Storage**: SQLite, with the `003_appearance.sql` migration (one column; now part of `migrations/001_initial.sql`). In the browser, the `semana-appearance` key in `localStorage`

**Testing**: pytest (operation, isolation, `/api/start`) and pytest-playwright (instant switch, second device, first paint and contrast)

**Target Platform**: local, for now

**Project Type**: web application (same process)

**Performance Goals**: change visible in ≤ 100 ms (SC-001), which is just changing attributes on `<html>`

**Constraints**: CSP with no inline script (`script-src` inherits `'self'`); offline; 360 px and keyboard

**Scale/Scope**: 1 column, 1 operation, 1 JS file of ~25 lines and ~40 lines recovered from the prototype

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How the plan complies | Status |
| --- | --- | --- |
| I. Fewer controls, more text | Panel in the profile menu, already planned in the prototype; no new control on screen | ✅ |
| II. The week is the unit | Does not apply | ✅ |
| III. Nothing gets lost | The change only touches `<html>` attributes: it does not redraw the task or touch the text being edited. A choice made offline goes through the queue | ✅ |
| IV. Each account's data is its own | The operation only writes to the session's account. There is a case in `test_isolation.py`. Values outside the lists are rejected | ✅ |
| V. Simplicity | One JSON column instead of a table; last write wins, with no revision ([R2](research.md)); no dependency | ✅ |
| VI. Tests where the rule is subtle | First paint without flashing, offline pending change versus the account cache, gradient contrast | ✅ |
| Product constraints | "Appearance belongs to the user": it does not change data. Keyboard, 360 px and screen reader come from the prototype (`role="radio"`) | ✅ |
| Workflow | Spec with no open-question markers; the difference from the prototype (saving in the account) is the owner's decision | ✅ |

**Re-check after Phase 1**: no violations. The contract only adds the `appearance` field to the responses and one new operation.

## Project Structure

### Documentation (this feature)

```text
specs/004-appearance/
├── plan.md
├── research.md          # R1–R4
├── data-model.md
├── quickstart.md
├── contracts/api.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
src/semana/
├── migrations/003_appearance.sql  # new: account.appearance (now in 001_initial.sql)
├── accounts.py                    # account_json with appearance; POST /account returns account_json
├── ops.py                         # account.appearance
└── static/
    ├── index.html, terms.html, privacy.html   # <script src="/js/appearance.js"> in <head>
    ├── sw.js                      # caches /js/appearance.js
    └── js/
        ├── appearance.js          # new: values, apply(), System mode, browser copy
        ├── data.js                # coalesce account.appearance; pending change beats the server
        └── app.js                 # prototype panel in the profile; apply on sign-in and on tab return

tests/
├── api/test_appearance_api.py     # new
├── api/test_isolation.py          # account.appearance case
└── e2e/test_appearance_panel.py   # new
```

**Structure Decision**: a single new code file, `appearance.js`. It is needed because the CSP does not let the page have an inline script and the appearance must apply before `app.js`, which is a module and runs after painting ([R1](research.md)).

## Complexity Tracking

No added dependency, layer or service.
