# Research: Accounts and weekly core

Technical decisions for feature 001. Each one records the choice, the reason and the rejected alternatives, as principle V of the constitution requires.

## R1. Server: Python 3.12 + FastAPI + uvicorn

- **Decision**: a single FastAPI process serves the JSON API and the client's static files.
- **Rationale**: Python with `uv`, `pydantic` and `pytest` is already the project owner's toolset. FastAPI validates each incoming operation with `pydantic` models, which covers validation at the trust boundary with no extra code. A single process removes CORS and cross configuration.
- **Alternatives**: Node + Hono/Express would allow sharing JS with the client, but the only code worth sharing is the sanitizer, and that is already covered by shared test cases (R11). Django brings an admin, ORM and templates that would go unused. The standard library's `http.server` is not fit for production.

## R2. Database: SQLite (WAL) with the standard library's `sqlite3` module

- **Decision**: one SQLite file in WAL mode, with `foreign_keys=ON`, `busy_timeout=5000` and `synchronous=NORMAL`. Migrations are numbered `.sql` files, applied at startup based on `PRAGMA user_version`. SQL is written by hand, with no ORM.
- **Rationale**: it needs no other service and uses no extra RAM on the VPS. Tests run on the same engine as production, and the backup is a copy of the file. Capacity: 1,000 simultaneous people writing at most every ~2 s give ≤ 500 small transactions per second in the worst case. SQLite in WAL on an SSD handles thousands. `BEGIN IMMEDIATE` serializes the rollover per account (R12). With explicit SQL, the `account_id = ?` filter is visible in every query (principle IV).
- **Alternatives**: PostgreSQL is one more service to run and only pays off with more than one application server. SQLAlchemy + Alembic is an extra layer for ~10 tables.
- **Known ceiling**: a single application server. Moving to PostgreSQL comes in when horizontal scaling is needed.

## R3. Client: JavaScript in ES modules, no build step, evolved from the prototype

- **Decision**: `specs/semana.html` is split into `index.html`, `app.css` and `js/*.js` modules served as is. The prototype's interface and gestures are reused, and its local storage layer (`persist`, `load`, `rollover`) is replaced by a data module that talks to the API (R5, R6).
- **Rationale**: the prototype is the behavior reference (constitution, development workflow) and is already plain JS with 250 KB of validated behavior. Rewriting with a framework would recreate that behavior and add a build and dependencies.
- **Alternatives**: React, Vue or Svelte would require a rewrite and a build. HTMX does not support offline editing.

## R4. Editor: `contenteditable` + `document.execCommand`, as in the prototype

- **Decision**: the prototype's editor (`format`, `applyLink`, `sanitizeHTML` etc.) is kept.
- **Rationale**: it already meets FR-031 to FR-038. `execCommand` is marked obsolete, but every current browser supports it and there is no standard replacement.
- **Alternatives**: ProseMirror or TipTap would be a heavy dependency and would require rewriting an editor that already works.
- **Risk**: if a browser removes `execCommand`, the swap is isolated in the editor module.

## R5. Offline operation: IndexedDB + service worker

- **Decision**:
  - **IndexedDB**, with two stores separated by account:
    - `cache`: latest responses from `/api/start` and from each week/project already opened.
    - `queue`: pending operations, in the order they were made.
  - **Service worker** of ~30 lines: for same-origin GETs outside `/api`, it tries the network first and, if that fails, uses the cache. `/api` responses do not go through it.
- **Rationale**: the US5 test closes and reopens the tab **with no network**, and without a service worker the page does not load. Trying the network first removes the need to version the cache on each deploy: online, the client is always up to date. The prototype already uses IndexedDB.
- **Alternatives**: without a service worker, US5 scenario 3 fails. Workbox would be a dependency for 30 lines. CRDT/Yjs merges automatically, and the spec asks to warn and let the person choose (FR-061).

## R6. Sync protocol: one route of ordered, idempotent operations

- **Decision**: every change is an operation (`task.title`, `subtask.done` etc.; list in [contracts/api.md](contracts/api.md)) and goes into the local queue before sending. The client sends the queue in batches to `POST /api/ops`. The server applies the operations in order and returns one result per operation. Reads use `GET /api/start` and `GET /api/week`.
- **Idempotency without an operation log**:
  - Project, task and subtask ids are UUIDs generated on the client, and creating an id that already exists does nothing.
  - Deleting something that does not exist returns `ok`.
  - Value operations (progress, importance, completion, order) set the final state instead of applying a difference.
  - A resend of text already saved arrives with a value equal to the current one and is accepted without conflict (R7).
- **Cross-account guarantee**: each batch carries the `account_id` that owns the queue. If it is not the session's account, the server refuses the whole batch with 409 (FR-058).
- **Rationale**: the queue maps directly to one route. With per-entity REST, each kind of pending change would need its own resend.
- **Alternatives**: per-resource REST, with more routes and case-by-case resending. A server-side log of operation ids would be one more table that idempotency by construction makes unnecessary.

## R7. Conflicts (FR-061): per-text-field revision

- **Decision**: `task.title`, `task.notes`, `subtask.text` and `week_notes.html` each have a `*_rev` counter.
  - The client sends `base_rev`, the last revision confirmed to it, read from the cache at send time and not when the operation was created.
  - If `base_rev` equals the current revision, the server saves and increments.
  - If it differs and the received value equals the current one, it responds `ok`: it is a resend.
  - Otherwise, it responds `conflict` with the current value and revision.
  - In the interface, a notice in the document itself, with no modal, shows both versions. Keeping the local version resends the operation with an updated `base_rev`. Keeping the other one replaces the local text. The discarded version stays copyable until the person closes the notice.
- **Rationale**: the conflict is per field, so editing different fields of the same task never conflicts. Since the client sends the queue in sequence, consecutive edits from the same device never conflict with each other.
- **Alternatives**: a per-row timestamp would create false conflicts between fields. A hash of the base value needs async `crypto.subtle` and gains nothing over a counter.
- **Progress, importance and order**: last writer wins, because the spec only requires a warning for texts.

## R8. Accounts and sessions

- **Password**: the standard library's `hashlib.scrypt`, with N=2¹⁴, r=8, p=5 (16 MiB per computation, an equivalent configuration listed by OWASP), a 16-byte salt and the parameters stored in the hash itself (`scrypt$n$r$p$salt$hash`) so the cost can be raised later. Minimum of 8 characters (FR-001).
- **Session**:
  - Random 32-byte token (`secrets`) in an `HttpOnly; Secure; SameSite=Lax; Path=/` cookie. The database stores only the token's SHA-256.
  - The session expires after 30 days without use. `used_at` is updated at most once per hour, to avoid writing on every request.
  - Logging out deletes the session. Resetting the password deletes all of the account's sessions (FR-003).
- **CSRF**: `SameSite=Lax` prevents the cookie from being sent on a POST coming from another site. On top of that, every route that changes data requires `Content-Type: application/json`, which another origin cannot send without a preflight.
- **Alternatives**: JWT would still need a table for "end other sessions". `argon2-cffi` would be one more dependency, and the standard library's scrypt meets the recommendation. `fastapi-users` brings more than the feature uses.
- **E-mail enumeration**: sign-up reveals that an e-mail already exists (a spec decision), so login response time does not need to be masked. Password recovery responds the same way in both cases (R10).

## R9. Login attempt lockout (FR-004)

- **Decision**: a `login_attempt` table records only failures (e-mail, IP, moment).
  - 5 failures for the same e-mail within 15 minutes lock that e-mail for 15 minutes.
  - 30 failures from the same IP within 15 minutes lock that IP.
  - A success clears the e-mail's failures, and records older than 7 days are removed in the route itself.
  - The IP comes from the `X-Forwarded-For` passed on by Caddy (`uvicorn --proxy-headers`).
- **Alternatives**: `slowapi` or Redis, a dependency or a service for a simple count.

## R10. Password recovery and e-mail

- **Decision**:
  - **Token**: 32 bytes, stored as SHA-256, valid for 1 hour and single-use.
  - **Same response**: `POST /api/password/request` always responds 202 and sends the e-mail in the background (`BackgroundTasks`), so that neither the response nor the timing reveals whether the e-mail exists.
  - **Sending**: the standard library's `smtplib` + `email.message`, with STARTTLS, to any SMTP provider configured through environment variables.
  - **Without SMTP configured** (development and tests): the link is written to the log.
- **Rationale**: any transactional e-mail provider (Amazon SES, Brevo, Resend, Postmark) accepts SMTP. That way the provider is deploy configuration, not code.
- **Alternatives**: a specific provider's SDK would tie the code to it.

## R11. HTML sanitizing (FR-035, FR-036)

- **Decision**:
  - **Allowlist**:
    - Tags: `p`, `h2`, `h3`, `ul`, `ol`, `li`, `strong`, `em`, `mark`, `a`, `br`.
    - Attribute: only `href` on `a`.
    - Schemes: `http`, `https`, `mailto` and `file`.
  - **On the server**: `nh3` (a binding of `ammonia`, in Rust) on every save, with that list.
  - **On the client**: the prototype's `sanitizeHTML` on paste and on display.
  - **Parity**: one case file (`tests/fixtures/html_cases.json`, with input and expected output, including Google Docs pastes and XSS vectors) applies to both sanitizers. The client's `sanitizeHTML` transforms the structure (Google Docs highlights become `mark`, `div` becomes `p`), and `nh3` only filters. So the property under test is not "same output", but two guarantees:
    - the client's expected output is a fixed point of `nh3`: the server never changes what the client produces;
    - no input, even through `nh3` alone, lets through a tag, attribute or scheme outside the list.
- **Rationale**: a hand-written HTML sanitizer in Python would be new security code. `nh3` is small, maintained and has no transitive dependencies. The client's sanitizer already exists and handles Google Docs pastes.
- **Alternatives**: `bleach` is deprecated. DOMPurify on the client would replace a sanitizer that already works.

## R12. Weekly rollover on the server (FR-045 to FR-048)

- **Decision**: the rollover runs on the server, on demand, at the start of `GET /api/start` and `GET /api/week`, in one `BEGIN IMMEDIATE` transaction per account:
  1. `current` = Monday 00:00 of today's date in the account's time zone.
  2. While `account.processed_week + 7 days < current`:
     1. `w` = `processed_week + 7`.
     2. Save `snapshot(account, w)` with the full copy of the tasks of week `w`, across all projects.
     3. Move the tasks of `w` with progress below 100 to `w + 7`, at the top and in the order they were in. Tasks already in `w + 7` move down `k` positions.
     4. Increment `weeks_open` and write "Carried over from the week of YYYY-MM-DD" to the log.
     5. Set `processed_week = w`.
  3. At sign-up, `processed_week` starts at the week before the sign-up week.
- **Idempotency**: a second device waits for the lock (`busy_timeout`), rereads `processed_week` and finds nothing to do (SC-006).
- **With the app open**: every minute, and when coming back to the tab, the client computes the current Monday in the account's time zone (`Intl`). If it changed, it reloads `/api/start` (FR-047: within 1 minute). The server's clock is the one that decides: the client applies to its own clock the difference to the `now` field of `/api/start`.
- **Rationale**: with several devices, a client-side rollover (as in the prototype) would be run by each of them. On the server, it happens only once.
- **Alternatives**: a global cron would go through every account, including inactive ones, and would still need the on-demand check for whoever opens the app right after midnight.

## R13. Closed weeks and late operations

- **Decision**:
  - **Read-only** (FR-048) is an interface rule, which shows the snapshot. The server keeps accepting changes to existing tasks and to week notes, whatever the week.
  - **Late operation**: an edit made offline on Sunday and sent on Monday is saved, not refused.
  - **Late creation**: a `task.create` for a week already closed, created offline before the rollover, is saved in the current week, as FR-027 requires for past weeks.
- **Rationale**: principle III. Refusing a late operation would lose text. The snapshot is immutable, so writing to the live record does not change what the closed week shows.
- **Alternatives**: refusing with "read-only" would lose the edit.

## R14. Time zone and week identifier

- **Decision**: the account's time zone comes from `Intl.DateTimeFormat().resolvedOptions().timeZone` at sign-up and is validated against `zoneinfo.available_timezones()`. If it is invalid, the sign-up is refused. The week is identified by the ISO date of its Monday (`2026-10-26`): it sorts as text and adds days with `datetime.date`.
- **Alternatives**: the ISO week (`2026-W44`) would need conversions at year boundaries. A per-device time zone would make each device roll the week over at a different time.

## R15. Tests (principle VI)

- **Decision**: `pytest` for everything.
  - **API**: `fastapi.testclient` (uses `httpx`), with a temporary database per test and an injectable clock. The `semana.clock.now()` function is replaced with `monkeypatch` in the API tests. In development and in browser tests, it reads `SEMANA_NOW`, which is ignored when `SEMANA_SECURE_COOKIE=1`, that is, in production.
  - **Browser**: `pytest-playwright` with Chromium, against the real server on a local port:
    - "Another device" is a second browser context.
    - Connection drops use `context.set_offline`.
    - The passing of time uses `page.clock`.
    - Mobile is a 360 px viewport with touch.
  - **Pure client functions** (link and path conversion, week calculation, sanitizing): tested in the browser with `page.evaluate`, with no second test runner.
  - **Isolation test** (SC-005): goes through the union of operation types and every `GET` route. If someone adds an operation without an isolation case, the test fails.
- **Alternatives**: Jest or Vitest would need Node and a second runner. Selenium is slower and does not emulate offline mode or the clock.

## R16. Hosting and backups

- **Decision**:
  - **Server**: a Linux VPS with at least 1 vCPU and 1 GB of free RAM. uvicorn runs with 2 workers under systemd, behind Caddy (automatic HTTPS through Let's Encrypt, reverse proxy).
  - **Backup**: daily, with the `sqlite3.Connection.backup` API (`python -m semana.backup DESTINATION`), triggered by a systemd timer. 30 days are kept, which meets the spec's assumption about deletion.
- **Rationale**: SQLite is on the same disk, so there is no managed database or container to run. Caddy handles TLS and headers in a few lines.
- **Alternatives**:
  - Docker Compose is an extra layer for a single process. It comes in when there is more than one service.
  - A PaaS (Fly.io, Render) would need a persistent volume for SQLite and would have a recurring cost. It is viable later.
- **Open**: which VPS to run on and the SMTP provider. Both are configuration and do not change the code.

## R17. Security headers

- **Decision**: the server sends the following headers:
  - `Content-Security-Policy: default-src 'self'; img-src 'self' data:; font-src 'self' data:; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'`. There are no inline scripts, because the prototype's inline script becomes a file. Inline styles are allowed because the cards get the progress color in `style`.
  - `Referrer-Policy: same-origin`, `X-Content-Type-Options: nosniff` and `Strict-Transport-Security`, the last one through Caddy.
- **Rationale**: it is the second barrier against XSS, on top of sanitizing (principle IV).

## R18. Legal texts

- **Decision**: draft texts in [legal/terms-of-use.md](legal/terms-of-use.md) and [legal/privacy-policy.md](legal/privacy-policy.md), with `[IN BRACKETS]` markers for the owner to fill in. Once reviewed, they become the static pages `/terms` and `/privacy`. Sign-up shows "By creating an account, you accept the Terms of Use and the Privacy Policy" with links to both.
- **Legal basis**: performance of a contract. That is why there is no consent checkbox.
- **Pending from the owner**:
  - Identity of the controller and of the data protection officer (encarregado).
  - Hosting and e-mail providers, and their countries.
  - Whether the Marco Civil (art. 15) applies, which changes the retention of access logs. If it applies, keeping Caddy's access log (IP, date and time) for 6 months with rotation is enough, with no new table.
  - Review by a lawyer.
