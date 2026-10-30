# Implementation Plan: Prototype import and backup

**Branch**: `005-import-backup` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-import-backup/spec.md`

## Summary

Export and import the whole account.

- **Server**: a new module, `backup.py`, with two routes.
  - `GET /api/backup` builds the file in the app's format.
  - `POST /api/backup` validates everything with pydantic and swaps, in a single transaction, the account's data for the file's. All IDs are generated again ([R2](research.md)). Then the rollover runs.
- **Client**: the prototype's Files menu comes back to the header (later moved into the profile menu, as its BACKUP section). A prototype backup (v1 or v2) is converted in the browser with the prototype's own code (`migrate`, `normalize`, `validateState`) and then to the app's format ([R1](research.md)). Both kinds of file go to the same route.

## Technical Context

**Language/Version**: Python 3.12; JavaScript ES2022 with no build (same as 001)

**Primary Dependencies**: none new

**Storage**: SQLite, no schema change

**Testing**: pytest (round trip, invalid files, all or nothing, isolation, sanitizing, rollover) and pytest-playwright (prototype conversion, menu flow, download)

**Target Platform**: local, for now

**Project Type**: web application (same process)

**Performance Goals**: import a 2-year backup (~1,500 tasks) in < 30 s (SC-002). In practice, it is one `executemany` per table

**Constraints**: all or nothing; no other account touched; same sanitizing as the app; keyboard and 360 px

**Scale/Scope**: 2 routes, ~200 lines of Python and ~120 of JS, half of them copied from the prototype

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How the plan complies | Status |
| --- | --- | --- |
| I. Fewer controls, more text | The prototype's Files menu, without the items that only made sense for the local file | ✅ |
| II. The week is the unit | Snapshots come along. The rollover runs after the import, from the file's processed week | ✅ |
| III. Nothing is lost | Full validation before touching any data. Explicit confirmation with the count of discarded pending changes. A single transaction | ✅ |
| IV. Each account's data is its own | The routes use only `account["id"]`. New IDs on every import, so a file with another account's IDs does not collide. There is an isolation test | ✅ |
| V. Simplicity | No new table. Reuses the validation types from `ops.py`, the sanitizing, the rollover and the prototype's import code | ✅ |
| VI. Tests where the rule is subtle | Round trip, all or nothing, repeated IDs, v1, sanitizing | ✅ |
| Product constraints | pt-BR (later English with a pt-BR translation); the menu and the confirmation stay inside the menu, no modal | ✅ |
| Workflow | Spec with no open-question markers. The owner's decisions are in Assumptions | ✅ |

**Re-evaluation after Phase 1**: no violations.

## Project Structure

### Documentation (this feature)

```text
specs/005-import-backup/
├── plan.md
├── research.md          # R1–R4
├── data-model.md        # file format
├── quickstart.md
├── contracts/api.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/semana/
├── backup.py                      # new: GET and POST /api/backup
├── app.py                         # includes the routes
└── static/js/
    ├── pure.js                    # + assignOrder, migrate, normalize, validateState (prototype), fromPrototype, readBackup, backupSummary
    └── app.js                     # Files menu, export, import with confirmation

tests/
├── api/test_backup_api.py         # new
├── api/test_isolation.py          # + import with another account's IDs
├── fixtures/prototype_v1.json, prototype_v2.json   # new
└── e2e/test_backup_menu.py        # new
```

**Structure Decision**: one new server module, `backup.py`. It holds the per-account export and import; a backup of the whole database, planned for deployment (R16 of 001), would live outside it.

## Complexity Tracking

No additions.
