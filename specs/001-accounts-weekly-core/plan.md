# Implementation Plan: Accounts and weekly core

**Branch**: `001-accounts-weekly-core` | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-accounts-weekly-core/spec.md`

## Summary

Turn the local prototype (`specs/semana.html`) into a hosted web app, with individual, private accounts, that keeps working when the connection drops.

- **Server**: one Python process (FastAPI) with SQLite. It stores each account's data, applies the weekly rollover exactly once per account and receives changes through a route of ordered, idempotent operations.
- **Client**: the prototype itself, split into ES modules with no build. The local storage layer is replaced by a cache and a send queue in IndexedDB, with a service worker that lets the app reopen offline.
- **Conflicts**: texts edited on two devices are detected by a per-field revision and resolved by the person (FR-061).

## Technical Context

**Language/Version**: Python 3.12 (server); JavaScript ES2022 in native modules, no build (client)

**Primary Dependencies**:

- Server: FastAPI, uvicorn and nh3.
- From the standard library: `sqlite3`, `hashlib.scrypt`, `secrets`, `smtplib`, `zoneinfo`.
- Development: pytest, httpx, pytest-playwright.

**Storage**: SQLite 3 in WAL mode on the server; IndexedDB on the client (cache + operation queue)

**Testing**: pytest. API through `fastapi.testclient`; browser through pytest-playwright (Chromium), with lost connection, simulated clock and a 360 px viewport

**Target Platform**: Linux VPS behind Caddy; current browsers on desktop and mobile (Chrome, Edge, Firefox, Safari)

**Project Type**: web application (JSON API + static client served by the same process)

**Performance Goals**: week usable ≤ 2 s after logging in (SC-002); text saved ≤ 3 s after typing stops (SC-003); 1,000 simultaneous people on a 1 vCPU/1 GB VPS (SC-007)

**Constraints**:

- Offline editing, with in-order sending on reconnect.
- No modals.
- HTML restricted by an allowlist.
- Everything operable by keyboard and usable at 360 px.
- UI in pt-BR. (This was the state at the time; the UI was later changed to English by default with a Brazilian Portuguese translation, picked from the browser language or the profile "Language" setting, in `src/semana/static/js/i18n.js`.)

**Scale/Scope**: 10 tables, 13 operation types, 9 API routes and a single-page client derived from a 250 KB prototype

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How the plan meets it | Status |
| --- | --- | --- |
| I. Fewer controls, more text | The prototype's interface is kept. The only additions are what the account requires: login, sign-up and password screens (pages, not modals), the profile menu and the conflict notice, which sits inside the document. No management features | ✅ |
| II. The week is the unit | Rollover on the server, in one transaction per account. Idempotent, processes all pending weeks and never pulls future tasks forward (R12). Closed weeks are read-only in the interface (R13) | ✅ |
| III. Nothing gets lost | Saving while typing. The IndexedDB queue survives closing the tab (R5), and the footer shows saved, saving, offline or failed. Conflicts are never resolved silently (R7), and late operations are saved, not refused (R13) | ✅ |
| IV. Each account's data is its own | `account_id` in every table and every query, checked on the server. An isolation test walks through every operation and route and fails if a new operation shows up without coverage (R15). Sanitizing with `nh3` on save and on the client on display (R11). CSP with no inline script (R17). Passwords with scrypt (R8) | ✅ |
| V. Simplicity | One process and one database file, no build, ORM or external queue. Each new dependency and layer is justified in [Complexity Tracking](#complexity-tracking) | ✅ |
| VI. Tests where the rule is subtle | Automated tests for rollover, sanitizing (with parity between server and client), links and paths, isolation and sending after an outage ([quickstart](quickstart.md#automated-tests)). Recurrence and search are not part of this feature | ✅ |
| Product constraints | pt-BR (later English with a pt-BR translation); web with first-class desktop and mobile; keyboard and 360 px tested in Playwright (SC-008); appearance stays out of the data | ✅ |
| Development workflow | The spec has no open-question markers, so `/speckit-clarify` does not apply. The departures from the prototype (server-side rollover, accounts, conflict) are in the spec | ✅ |

**Re-evaluation after Phase 1**: the design in [data-model.md](data-model.md) and [contracts/api.md](contracts/api.md) introduces no violations.

- Isolation became concrete: `account_id` in every table, including child tables.
- The single operations route reduced the API surface.
- The decision not to refuse late operations (R13) strengthened principle III.

## Project Structure

### Documentation (this feature)

```text
specs/001-accounts-weekly-core/
├── plan.md              # this file
├── research.md          # Phase 0: decisions R1–R18
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/api.md     # Phase 1
├── legal/               # draft terms and privacy texts (R18)
├── checklists/          # spec quality checklist
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
pyproject.toml
src/semana/
├── app.py               # FastAPI routes, security headers, static files
├── db.py                # SQLite connection and migrations via PRAGMA user_version
├── migrations/
│   └── 001_initial.sql
├── clock.py             # injectable now() (R15)
├── accounts.py          # sign-up, login, sessions, password, lockout, deletion
├── reads.py             # /api/start and /api/week
├── ops.py               # pydantic models for the operations and in-order application
├── rollover.py          # weekly rollover (R12)
├── sanitize.py          # nh3 with the allowlist (R11)
├── mail.py              # sending through smtplib (R10)
├── backup.py            # python -m semana.backup DESTINATION (R16); postponed, today it holds the feature 005 backup routes
└── static/
    ├── index.html       # app (derived from specs/semana.html)
    ├── (password.html)  # planned; /password ended up serving index.html, which draws the new-password form
    ├── terms.html
    ├── privacy.html
    ├── app.css
    ├── sw.js            # service worker: network first, cache as fallback (R5)
    └── js/              # prototype modules + data.js (cache, queue, sending, conflicts)

tests/
├── conftest.py          # app with a temporary database, clock, server for e2e
├── fixtures/html_cases.json
├── api/                 # isolation, rollover, ops (idempotency and conflict), accounts, sanitizing
├── e2e/                 # offline, keyboard and 360 px, links and paths, pasting, client-side sanitizing
└── load.py              # SC-007

deploy/                  # POSTPONED: for now the app only runs locally (decision of 2026-10-27)
├── Caddyfile
├── semana.service
├── semana-backup.service
└── semana-backup.timer
```

**Structure Decision**: a single Python project, with the static client inside the package (`src/semana/static`) and served by the same process. There is no frontend/backend split, because the client has no build and no dependencies of its own. The `static/js` modules come out of the prototype's script; the exact split is left to `/speckit-tasks`.

## Complexity Tracking

Principle V requires justifying each new dependency, layer or service compared with the prototype, which had none.

| Addition | Why it is needed | Simpler alternative rejected because |
| --- | --- | --- |
| Server (FastAPI + uvicorn) | Accounts and data reachable from any device are the goal of the feature | `http.server` is not fit for production. FastAPI validates the operations with pydantic with no extra code |
| `nh3` | Server-side sanitizing is required by principle IV | A hand-written sanitizer would be new security code with no track record |
| Service worker | Reopening the tab offline (US5 scenario 3, SC-004) | Without it, the page does not load without a network |
| Queue + cache in IndexedDB | Nothing gets lost during outages (FR-056) | Writing straight to the API loses the edit when the network drops |
| Caddy | HTTPS and headers | uvicorn with its own certificate would need manual renewal |
| pytest-playwright | Principle VI tests include browser behavior (connection drop, client-side sanitizing, links) | API-only tests do not cover the queue or the editor. Jest would need Node and a second runner |
