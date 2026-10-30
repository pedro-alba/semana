---

description: "Implementation tasks for feature 001: accounts and weekly core"
---

# Tasks: Accounts and weekly core

**Input**: Design documents from `/specs/001-accounts-weekly-core/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md)

**Tests**: required where the rule is subtle (constitution, principle VI): isolation between accounts, rollover, sanitizing, links and paths, sending after an outage, idempotency and conflict of operations. Simple UI does not get a per-component test.

**Organization**: tasks grouped by user story. US1 (account) is a real prerequisite for the others: without an account there is no data.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task).
- **[Story]**: story from the spec (US1 to US6).
- Paths are relative to the repository root (`semana/semana/`).

## References used in the tasks

- **Prototype**: `specs/semana.html`.
  - Lines 9–685: CSS.
  - Lines 692–2015: script, wrapped in an IIFE.
  - The line numbers quoted are from the original file.
- **Task adapter** (server → prototype format), defined in T016:

  ```
  {id, projectId: project_id, week, title, description: notes,
   important, progress, order: position, createdAt: created_at,
   lastActivity: updated_at, carries: weeks_open - 1,
   subtasks: [{id, text, done: !!done_at, createdAt: created_at,
               doneAt: done_at || '', rev: text_rev}],
   log: [{id, at, kind, text}],
   rev: {title: title_rev, notes: notes_rev}}
  ```

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Python project and static client extracted from the prototype.

- [X] T001 Create `pyproject.toml` at the root and the empty file `src/semana/__init__.py`. Then run `uv sync` and `uv run playwright install chromium`. `pyproject.toml` must have:
  - project `semana`, with `requires-python = ">=3.12"`;
  - dependencies `fastapi`, `uvicorn` and `nh3`;
  - `[dependency-groups] dev = ["pytest", "httpx", "pytest-playwright", "ruff"]`;
  - build with `hatchling` and `packages = ["src/semana"]`;
  - `[tool.pytest.ini_options] testpaths = ["tests"]`;
  - `[tool.ruff] line-length = 100`.
- [X] T002 [P] Copy unchanged the contents of `<style id="app-style">` (prototype lines 9–685, including the base64 fonts) to `src/semana/static/app.css`. On the first line, put the comment `/* ponytail: styles for all themes kept for feature 004; this feature only uses dark Graphite */` (today it reads `/* ponytail: styles for every theme kept for feature 004 */`).
- [X] T003 [P] Create `src/semana/static/index.html`:
  - Copy the prototype's `<head>` (lines 1–7) and replace `<html lang="pt-BR">` with `<html lang="pt-BR" data-theme="graphite" data-mode="dark" data-mode-pref="dark" data-font="theme" data-palette="classic">` (FR-065). This replacement takes the place of the `theme-boot` script, which must not be copied. (At the time the UI was pt-BR only; since the interface moved to English with a Brazilian Portuguese translation, both the prototype and `index.html` use `lang="en"`, and `i18n.js` sets `lang` at runtime.)
  - Add `<link rel="stylesheet" href="/app.css">` to the `<head>`.
  - In the `<body>`, put `<div id="app"></div>`, `<div id="toast" role="status" aria-live="polite"></div>` and `<div id="sr-status" class="sr-only" aria-live="polite"></div>` (lines 688–690) and `<script type="module" src="/js/app.js"></script>`.
  - Do not use inline scripts, because of the CSP (R17).
- [X] T004 [P] Create `src/semana/static/js/pure.js` as an ES module that `export`s the prototype's pure utilities, copied without changing the logic:
  - Utilities from lines 694–709: `DAY`, `HL`, `esc`, `civil`, `dateKey`, `today`, `addDays`, `weekOf`, `dayDiff`, `validDate`, `clone`, `fmt` and `stamp`.
  - `ordered` (line 712).
  - The links section from lines 765–802: `encPath`, `parseLink`, `isFileLink`, `nativePath`, `linkLabel`, `fileName` and `autoLink`.
  - The sanitizing section from lines 806–877: `DROP_TAGS`, `BLOCK_TAGS`, `BLOCK_SELECTOR`, `clearColor`, `nextFormat`, `sanitizeHTML`, `toEditor`, `textToHtml` and `plainText`, plus the inverse function of `toEditor`, if there is one.
  - Do not copy what this feature does not use: `assignOrder`, `rollover`, `occurrences`, `layoutEvents`, `textOf`, `fold`, `weekday`, `monthShort` and `fmtDay`. If `fmt` or another kept function depends on one of them, copy only the dependency.
- [X] T005 Create `src/semana/static/js/app.js` with the prototype's script (lines 693–2014), without the IIFE and with `import { … } from './pure.js'` in place of the definitions moved in T004.
  - **Remove** what is outside feature 001:
    - Calendar: `events()`, `openEvent`, `eventEditor`, `dueEventHTML`, `drawCalendar`, `eventValues`, `syncEventFrequency`, `screen === 'calendar'` and the `event`, `slot` and `open-location` handlers.
    - Due dates: `dueState`, `dueShort`, `setDue`, the `due-pick` handler, the due date on the card and in `metaHTML`, and `!t.due` in `isBlank`.
    - Search (lines 1630–1727): `searchItems` through `revealIn` and the Ctrl+Space shortcut.
    - Appearance (lines 991–1025): `PREF_KEY` through `prefsHTML`, `applyMode` and the `pref` handler.
    - Files menu: `download`, `prototypeSource` and the export, import and "Start without examples" handlers.
    - Legacy data: `seed`, `migrate`, `normalize` and `validateState`.
  - **Header** (`headerHTML`, line 1084): keep only the brand, the Tasks navigation button and the `<details class="menu profile-menu">`, still with empty contents, which T026 fills in (FR-010). Take out the Calendar button, the search hint and the Files menu.
  - **Persistence**: keep `persist`, `load` and the calls to `rollover` for now. T016 replaces them.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: database, server, session, reads, operations route and the client's data layer.

**⚠️ CRITICAL**: no story starts before this phase.

- [X] T006 Create `src/semana/migrations/001_initial.sql` with the 10 tables from [data-model.md](data-model.md), with literal columns and constraints. Every column is `NOT NULL`, except those marked NULL in the model.
  - **account**: `email TEXT NOT NULL UNIQUE COLLATE NOCASE`.
  - **Revisions**: `title_rev`, `notes_rev`, `text_rev` and `week_notes.rev` are `INTEGER NOT NULL DEFAULT 0`.
  - **task**: `progress INTEGER NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100)`, `important INTEGER NOT NULL DEFAULT 0 CHECK (important IN (0,1))` and `weeks_open INTEGER NOT NULL DEFAULT 1`.
  - **Foreign keys**:
    - every FK to `account(id)` uses `ON DELETE CASCADE`;
    - `subtask.task_id` and `log_entry.task_id` reference `task(id)` with `ON DELETE CASCADE`;
    - `task.project_id` and `week_notes.project_id` reference `project(id)` with `ON DELETE CASCADE`.
  - **Composite primary keys**: `week_notes` uses `PRIMARY KEY (account_id, project_id, week)` and `snapshot` uses `PRIMARY KEY (account_id, week)`.
  - **Indexes**: `CREATE INDEX task_week ON task(account_id, project_id, week, position)` and indexes on `subtask(task_id)`, `log_entry(task_id)` and `login_attempt(email)`.
- [X] T007 Create `src/semana/db.py`:
  - `connect(path=os.environ.get("SEMANA_DB", "semana.sqlite3"))` opens the connection with `isolation_level=None`, `row_factory=sqlite3.Row`, `check_same_thread=False` and the PRAGMAs `journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout=5000` and `synchronous=NORMAL`.
  - `migrate(con)` applies, in order, the `migrations/NNN_*.sql` files with NNN greater than `PRAGMA user_version` and updates `user_version`.
  - The context manager `transaction(con)` runs `BEGIN IMMEDIATE` and `COMMIT`, or `ROLLBACK` on an exception.
  - The FastAPI dependency `connection()` opens one connection per request and closes it at the end, with `yield`.
- [X] T008 [P] Create `src/semana/clock.py`:
  - `now()` returns a timezone-aware UTC `datetime`. If `SEMANA_NOW` is set **and** `SEMANA_SECURE_COOKIE == "0"`, it returns that fixed instant (R15).
  - `iso(dt)` formats as `YYYY-MM-DDTHH:MM:SSZ`.
  - `monday(dt, timezone)` returns the ISO date of the Monday of `dt`'s week in the given IANA time zone (`zoneinfo`).
  - `is_monday(s)` tells whether `s` is a valid ISO date that falls on a Monday.
  - `add_days(s, n)` adds `n` days to an ISO date.
- [X] T009 Create `src/semana/app.py` with `create_app()` and `app = create_app()`:
  - **lifespan**: calls `migrate` on a connection.
  - **Headers middleware** (R17):
    - `Content-Security-Policy: default-src 'self'; img-src 'self' data:; font-src 'self' data:; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'`;
    - `Referrer-Policy: same-origin`;
    - `X-Content-Type-Options: nosniff`.
  - **Content type middleware**: `POST` and `DELETE` under `/api` without `Content-Type: application/json` get 415 `{"error": "bad_content_type"}`.
  - **Validation error**: the `RequestValidationError` handler responds 422 `{"error": "invalid", "fields": [<field name>…]}`.
  - **Static files**:
    - `GET /password` serves `static/index.html`;
    - `GET /terms` serves `static/terms.html` and `GET /privacy` serves `static/privacy.html`;
    - last comes the `StaticFiles(directory=<package>/static, html=True)` mount at `/`.
  - **Routers**: include the `APIRouter`s from `accounts`, `reads` and `ops`.
- [X] T010 Create `src/semana/accounts.py` (core):
  - **Password**: `hash_password(s)` uses `hashlib.scrypt(n=2**14, r=8, p=5, maxmem=64 * 1024 * 1024, dklen=32)` with salt `secrets.token_bytes(16)` and stores it in the format `scrypt$n$r$p$<salt b64>$<hash b64>`. `check_password(s, h)` uses `hmac.compare_digest`.
  - **Create session**: `create_session(con, account_id) -> token` generates `secrets.token_urlsafe(32)` and stores the hex SHA-256 in `session` with `created_at` and `used_at` equal to `now`.
  - **Cookie**: `set_cookie(resp, token)` sets `semana_session` with `HttpOnly`, `SameSite=Lax`, `Path=/` and `max_age=30 days`. The cookie is `Secure`, unless `SEMANA_SECURE_COOKIE == "0"`.
  - **`current_account` dependency**: reads the cookie and looks up the session. The session is valid if `used_at > now - 30 days` (FR-002). If `used_at` is more than 1 hour old, it updates the field. Returns the `account` row or raises 401 `{"error": "no_session"}`.
- [X] T011 In `src/semana/accounts.py`, create the sign-up, login and logout routes according to [contracts/api.md](contracts/api.md):
  - **`POST /api/account`**:
    - Validation: e-mail with `@`, up to 254 characters, no leading or trailing spaces; password "≥ 8" characters; time zone in `zoneinfo.available_timezones()`. Failures give 422.
    - E-mail already registered, case-insensitive: 409 `email_taken`.
    - Saves the account with `processed_week = add_days(monday(now, timezone), -7)` and the projects "Personal" and "Work", in that order, with the same `created_at` (FR-007).
    - Creates the session and responds 201 `{"account": {id, email, timezone}}`.
  - **`POST /api/login`**: 200 with cookie, or 401 `credentials`.
  - **`POST /api/logout`**: deletes the session row, removes the cookie and responds 204.
- [X] T012 Create `src/semana/reads.py` with the routes from [contracts/api.md](contracts/api.md#reads). **Every query filters by `account_id`.**
  - **`GET /api/start`**: returns `account`, `current_week = monday(now, timezone)`, `now = iso(now())` and the `projects` ordered by `created_at` and then by `rowid`.
  - **`GET /api/week?project=&week=`**:
    - 422 if `week` is not a Monday. 404 `not_found` if the project does not belong to the account.
    - `state` comes from comparing with `current_week`: `past`, `current` or `planning`.
    - For `past`: `tasks` = items of `snapshot.tasks` with the requested `project_id`, or `[]`.
    - In the other states: tasks of `(account, project, week)` ordered by `position`, each with `subtasks` (by `created_at`) and `log` (by `at`), in the contract format.
    - `notes` = `{html, rev}` from `week_notes`, or `{"html": "", "rev": 0}`.
  - **Shared format**: the function `task_json(con, row)` builds that format and is reused by the snapshot (T041).
- [X] T013 Create `src/semana/ops.py` (structure):
  - **Registry**: a dictionary `OPS: dict[str, tuple[type[BaseModel], Callable]]`, filled in by the `@operation(name, Model)` decorator. The handlers are added in US2, US3 and US6.
  - **`POST /api/ops`**:
    - Body `{"account_id": str, "ops": list[dict]}`, with at most 200 operations. Above that, 422.
    - If `account_id` differs from the session's account, 409 `{"error": "wrong_account"}` and nothing is applied.
    - Each operation, in order: an unknown name or a validation failure gives `{"status": "invalid", "fields": [...]}`. Otherwise, the handler runs inside `transaction(con)` with the signature `handler(con, account, model) -> dict` and returns `{"status": "ok" | "conflict" | "not_found", ...}`.
    - Response 200 `{"results": [...]}`, in the same order as the operations.
  - **Helper functions**: `owned(con, table, id, account_id)` returns the row or `None`. `touch_task(con, task_id)` sets `updated_at = now`.
- [X] T014 [P] Create `tests/conftest.py`:
  - **`app_client`**: `monkeypatch.setenv("SEMANA_DB", tmp_path/"t.sqlite3")` and `SEMANA_SECURE_COOKIE=0`, then `TestClient(create_app())` used as a context manager. Exposes a factory to create extra clients on the same app, with separate cookies.
  - **`clock`**: replaces `semana.clock.now` with a mutable instant. The default is `2026-10-27T12:00:00Z`, a Tuesday. Exposes `set(iso)` and `advance(**timedelta)`.
  - **`new_account(client, email, timezone="America/Sao_Paulo")`**: signs up the account and returns the JSON from `/api/start`.
  - **`server`** (for e2e): starts `uvicorn.Server` in a thread, on a free port, with a temporary database and `SEMANA_SECURE_COOKIE=0`, and returns the base URL.
- [X] T015 [P] Create `src/semana/static/js/data.js`, the client's data module (R5, R6, R7).
  - **IndexedDB**: database `semana` v1 with the stores `cache` (`keyPath: ['account_id', 'key']`) and `queue` (`autoIncrement`, index `account_id`).
  - **`api(method, path, body)`**: same-origin `fetch`, sending and receiving JSON.
    - A network failure throws `{kind: 'network'}`.
    - A 401 response throws `{kind: 'session'}`.
    - Otherwise it returns `{status, json}`.
  - **Reads with cache**:
    - `start()` calls `GET /api/start`, stores it in `cache` with the key `'start'` and saves `account.id` in `localStorage['semana-account']`, with `try/catch`. Without a network, it returns the cache.
    - `week(project, monday)` does the same with the key `week|<project>|<monday>`. Without a network and without a cache, it throws `{kind: 'offline'}` (FR-057).
    - `store(key, data)` writes to the cache.
  - **`enqueue(op)`**: writes `{account_id, op}` to the `queue` and schedules sending.
    - Text operations are `task.title`, `task.notes`, `subtask.text` and `week.notes`.
    - If the queue already has a not-yet-sent text operation of the same kind and target, `enqueue` only replaces its `value`, without changing its position. The target is the `id`, or `project_id + week` for `week.notes`.
  - **`send()`**: batches of up to 200 operations of the current account, in order, marking the ones in flight. For each result:
    - `ok`: deletes the operation. If a `rev` came back, adjusts the `base_rev` of the pending text operation with the same target and field and calls `onRev(op, rev)`.
    - `conflict`: deletes the operation and calls `onConflict(op, value, rev)`.
    - `not_found`: deletes the operation.
    - `invalid`: deletes the operation and changes the state to `failed`.
    - Network error: state `offline`. Retries on the `online` event and every 15 s.
    - 401 or 409 `wrong_account`: stops and calls `onSession()`.
  - **State and cleanup**:
    - `state()` returns `{kind: 'saved' | 'saving' | 'offline' | 'failed', pending}`, and `onState(cb)` reports changes.
    - `pending()` returns the number of operations in the queue.
    - `clearAccount(account_id)` erases the account's cache and queue.
  - **Accounts**: only the queue of the current `account_id` is read or sent (FR-058).
  - Comment in the code: `// ponytail: if the tab closes mid-send, the next edit of the same field may raise a false conflict; record op ids on the server if that shows up`.
- [X] T016 In `src/semana/static/js/app.js`, replace local persistence with the API:
  - **Remove** `DB_NAME`, `KEY`, `LEGACY_KEY`, `idbGet`, `load`, the storage part of `pruneBlank` and the calls to `rollover`.
  - **New `boot()`**:
    - `data.start()` builds `S = {week: current_week, projects: projects.map(p => ({id: p.id, name: p.name})), tasks: [], notes: {}, snapshots: {}}`.
    - `project` becomes the id of the first project. Keep `account` and `offset = Date.parse(now) - Date.now()`.
    - Load the displayed week with `data.week()` and pass each task through the **adapter** described at the top of this file.
    - `S.notes[week + '|' + project] = notes.html` and `S.notesRev[...] = notes.rev`.
    - If the `state` is `past`, the tasks go to `S.snapshots[week]`.
  - **Switching week or project** (week buttons, selector and brand): calls `data.week()` before `render()`.
  - **`persist()`**: now writes the current view back to the cache, in server format, with `data.store`. Writing to the server happens through the operations (US2+).
  - **Footer**: `#storage` follows `data.onState`:
    - "Saved";
    - "Saving…";
    - "Offline · N changes waiting to be sent";
    - "Couldn't save".

    The footer keeps "One day at a time." (FR-010, FR-055).
  - **Ids**: replace `uid()` with `crypto.randomUUID()`.
- [X] T017 In `src/semana/static/js/app.js`, create the login screens, drawn in `#app` in place of the app (a page, not a modal). They are used when `start()` throws `session` and there is no cache.
  - **"Log in"**: e-mail, password, a Log in button and the links "Create account" and "Forgot password". The "Forgot password" link stays hidden until T025.
  - **"Create account"**: e-mail and password, with the hint "At least 8 characters", and the time zone from `Intl.DateTimeFormat().resolvedOptions().timeZone`. It has the sentence "By creating an account, you accept the <a href="/terms">Terms of Use</a> and the <a href="/privacy">Privacy Policy</a>."
  - **Messages**:
    - `credentials`: "Wrong e-mail or password."
    - `email_taken`: "This e-mail already has an account. Forgot your password?", with a link to recovery.
    - `invalid`: message on the matching field.
  - **After success**: runs `boot()`.
  - **Accessibility**: the fields have a `<label>` and the screen works with the keyboard alone.

**Checkpoint**: `uv run uvicorn semana.app:app --reload` works, sign-up leads to the empty current week in Personal, and navigating between weeks and projects reads from the server.

---

## Phase 3: User Story 1 - Have my Semana on any device (Priority: P1) 🎯 MVP

**Goal**: full account lifecycle (recovery, lockout, deletion, profile) and verified isolation.

**Independent Test**: create account A and a task, log out and log in from another browser to see the task. Account B sees nothing from A, not even by direct address.

### Tests for User Story 1 ⚠️

> Write first and watch them fail.

- [X] T018 [P] [US1] Create `tests/api/test_accounts.py`, using the `app_client` and `clock` fixtures:
  - **Sign-up**: 201 with the Personal and Work projects. `A@x.com` after `a@x.com` gives 409. A 7-character password gives 422. Time zone `Mars/Base` gives 422.
  - **Log in and log out**: logging in and out work, and after logging out `GET /api/start` gives 401.
  - **Session**: with `advance(days=31)` without use, the session expires. With use every 29 days, it does not expire.
  - **Lockout**:
    - 5 wrong passwords for the same e-mail give 429 with `retry_at`, and access comes back after 15 min.
    - A success clears the e-mail's failures.
    - 30 failures from the same IP with different e-mails give 429.
  - **Recovery**:
    - `POST /api/password/request` responds 202 the same way for an existing and a non-existing e-mail.
    - The token is captured by replacing `semana.mail.send`.
    - The token works once, and the second time gives 400 `invalid_token`. It also gives 400 after 61 min.
    - Resetting makes the old client get 401.
  - **Delete account**:
    - Wrong password gives 403.
    - Right password gives 204, and no table keeps rows for that `account_id`. The check goes through `sqlite_master`.
    - The e-mail accepts sign-up again.
- [X] T019 [P] [US1] Create `tests/api/test_isolation.py` (SC-005, FR-005).
  - **GET routes**: with accounts A and B, `GET /api/week` with A's project, made in B's session, gives 404. B's `GET /api/start` lists only B's projects.
  - **Operations**:
    - The dictionary `CASES: dict[str, Callable[[a_data], dict]]` builds, for each operation, a payload that targets A's data.
    - The test is parametrized over `semana.ops.OPS`. For each operation, B sends the payload, the result must be `not_found` and A's `GET /api/week` must be identical before and after.
    - The test fails with the message "op without an isolation case: <name>" if `OPS` has an operation missing from `CASES`.
  - **Batch from another account**: a batch with A's `account_id` sent in B's session gives 409 `wrong_account`.

### Implementation for User Story 1

- [X] T020 [US1] In `src/semana/accounts.py`, apply the login lockout (FR-004, R9) in `POST /api/login`, before checking the password:
  - Each failure is written to `login_attempt` with the lowercase e-mail, the IP (`request.client.host`) and `now`.
  - Literal rule: "5 failures for the same e-mail within 15 minutes lock that e-mail for 15 minutes; 30 failures from the same IP within 15 minutes lock that IP; a success clears the e-mail's failures; records older than 7 days are removed" (the removal runs in the route itself).
  - The lockout responds 429 `{"error": "locked", "retry_at": iso}`, with the oldest failure in the window + 15 min.
- [X] T021 [P] [US1] Create `src/semana/mail.py` with `send(to, subject, text)`:
  - With `SEMANA_SMTP_HOST` set, it uses `smtplib.SMTP(host, int(SEMANA_SMTP_PORT or 587))` and `starttls()`. It runs `login(SEMANA_SMTP_USER, SEMANA_SMTP_PASSWORD)` if there is a user, and sends an `email.message.EmailMessage` with the sender from `SEMANA_SMTP_FROM`.
  - Without a host, it only logs the whole message with `logging.getLogger("semana").info`. This is the local mode.
- [X] T022 [US1] In `src/semana/accounts.py`, create the password recovery routes (FR-003, R10):
  - **`POST /api/password/request`**: **always** responds 202. If the account exists:
    - generates a `secrets.token_urlsafe(32)` token;
    - stores the SHA-256 in `password_token`, with `expires_at = now + 1h`;
    - schedules `BackgroundTasks` → `mail.send` with the subject "Reset your Semana password" and the link `f"{SEMANA_BASE_URL}/password#{token}"`.
  - **`POST /api/password/reset`**:
    - The token is valid if it exists, has a null `used_at` and `expires_at > now`. If not, 400 `invalid_token`.
    - A password with fewer than 8 characters gives 422.
    - If everything is right, it saves the new `password_hash`, fills in `used_at`, deletes **all** of the account's `session` rows and responds 204.
- [X] T023 [US1] In `src/semana/accounts.py`, create `DELETE /api/account` (FR-006):
  - Wrong password gives 403 `wrong_password`.
  - Right password: `DELETE FROM account WHERE id = ?` (the cascade erases the rest) and `DELETE FROM login_attempt WHERE email = ?`, then removes the cookie and responds 204.
- [X] T024 [P] [US1] Convert by hand [legal/terms-of-use.md](legal/terms-of-use.md) and [legal/privacy-policy.md](legal/privacy-policy.md) into `src/semana/static/terms.html` and `src/semana/static/privacy.html`:
  - Full pages: `<!doctype html>`, `lang="pt-BR"` (today `terms.html`/`privacy.html` are in English with `lang="en"`, and `terms.pt-BR.html`/`privacy.pt-BR.html` hold the Portuguese versions), `/app.css`, the same `data-*` attributes as `index.html` and a "← Back to Semana" link to `/`.
  - Keep the `[BRACKETS]` markers visible and remove the HTML comments.
  - Reading style: centered column with a `max-width` of about 70ch, in CSS in `app.css` itself with the `.legal-page` selector.
- [X] T025 [US1] In `src/semana/static/js/app.js`, create password recovery:
  - **"Forgot password"**: the e-mail form calls `POST /api/password/request` and always shows "If there is an account with this e-mail, we sent a link that is valid for 1 hour."
  - **`location.pathname === '/password'`**: the "New password" form reads the token from `location.hash.slice(1)` and calls `POST /api/password/reset`.
    - With 204, it shows "Password changed. Log in with your new password." and a link to `/`.
    - With 400, it shows "This link is invalid or has expired." and a link to request another one.
- [X] T026 [US1] In `src/semana/static/js/app.js`, create the profile menu in the header's `<details class="menu profile-menu">` (FR-010). It is a non-modal menu, which closes with Esc and with a click outside, and has the account e-mail and two actions:
  - **"Log out"**:
    - If `data.pending() > 0`, shows a confirmation in the menu itself: "N changes have not been sent yet and will be discarded. Log out anyway?" (FR-058).
    - Then calls `POST /api/logout`, `data.clearAccount(account.id)` and goes back to the login screen.
  - **"Delete account"**:
    - Opens in the menu itself a password field and the button "Delete account and all data", which calls `DELETE /api/account`.
    - With 403, shows "Wrong password".
    - With 204, calls `data.clearAccount` and goes back to the login screen.

**Checkpoint**: T018 and T019 pass (T019 only with the GET cases for now) and the US1 independent test works manually, creating the task in T030.

---

## Phase 4: User Story 2 - Plan and track the week's tasks (Priority: P1)

**Goal**: create projects and tasks, adjust progress and importance and reorder, all persisted.

**Independent Test**: create tasks in Personal in the current week and in a future one, adjust the progress until done, reorder, reload and check.

### Tests for User Story 2 ⚠️

- [X] T027 [P] [US2] Create `tests/api/test_ops.py` with the helper functions `ops(client, account_id, *items)` and `week(client, project, monday)` and these cases:
  - **Creation**:
    - `task.create` creates at the end of the open tasks, with `position = max + 1`.
    - Re-creating with the same id changes nothing.
    - Creating with a `week` before the current one saves in the current week (R13).
  - **Progress**:
    - Reaching `progress` 100 takes the task to the end of the done tasks.
    - Going back to 60 takes the task to the end of the open tasks (FR-024).
    - Values 101 and -1 give `invalid`.
  - **Reorder**:
    - `task.reorder` redistributes only the positions that the sent ids already hold and ignores unknown ids.
    - It does not change `updated_at` (FR-051).
  - **Update**: `task.important` and `task.progress` change `updated_at`.
  - **Deletion**: a repeated `task.delete` gives no error.
  - **Project**: `project.create` with the name `"  "` gives `invalid`, and with 61 characters too.
  - **Resend**: resending the same whole batch produces the same state.
- [X] T028 [P] [US2] In `tests/api/test_isolation.py`, add to `CASES` the entries `project.create` (id of one of A's projects), `task.create` (A's `project_id`), `task.progress`, `task.important`, `task.reorder` (A's project and ids) and `task.delete`.

### Implementation for User Story 2

- [X] T029 [US2] In `src/semana/ops.py`, create the handlers with `@operation`. The rules are in [contracts/api.md](contracts/api.md#operations).
  - **`project.create`**:
    - Fields: `id: UUID` and `name: str`, with the literal constraint "required, 1–60 characters after trimming leading and trailing spaces".
    - Uses `INSERT … ON CONFLICT(id) DO NOTHING`. If the id exists in another account, responds `not_found`.
  - **`task.create`**:
    - Fields: `id`, `project_id` (the account's) and `week`. The `week` must be a Monday; otherwise, `invalid`.
    - If `week < current_week`, saves in `current_week`.
    - Saves with `progress` 0, `position = max(position) + 1` in the project's week and `created_at = updated_at = now`.
  - **`task.progress`**:
    - Fields: `id` and `value: int`, with the constraint `CHECK (progress BETWEEN 0 AND 100)`.
    - If the value crosses 100 in either direction, `position = max + 1`. Touches the task.
  - **`task.important`**: fields `id` and `value: bool`. Touches the task.
  - **`task.reorder`**:
    - Fields: `project_id`, `week` and `ids: list[UUID]` with up to 1000 items.
    - Takes the current `position` values of the account's tasks in that project and week whose ids are in the list, sorts those values and reassigns them in list order. Does not touch the task.
  - **`task.delete`**: field `id`. Uses `DELETE … WHERE id = ? AND account_id = ?` and responds `ok` even if nothing was deleted.
- [X] T030 [US2] In `src/semana/static/js/app.js`, wire the changes to the operations. Each point keeps the local change and `persist()` and calls `data.enqueue`:
  - Creating a project with the + button produces `project.create` with `crypto.randomUUID()`.
  - `newTask` (line 1540) produces `task.create`. In a past week, the task goes to `S.week` (FR-027).
  - `commitProgress` (line 1455) produces `task.progress`.
  - The flag button produces `task.important`.
  - `finishSort` (line 1513) and `moveByKeyboard` (line 1521) produce `task.reorder`, with the affected group's ids already in the new order.
  - A blank task, when the person leaves it (`isBlank`, line 1049, without `due`), is removed locally and produces `task.delete` (FR-028).

**Checkpoint**: T027 passes, T019 passes with the new cases and the US2 independent test works manually.

---

## Phase 5: User Story 3 - Write in the task like in a document (Priority: P1)

**Goal**: title, sanitized rich notes, subtasks with a log, links and edit conflicts handled.

**Independent Test**: open a task, format the text, paste a passage from Google Docs, create and complete subtasks, add a website link and a file path, reload and check.

### Tests for User Story 3 ⚠️

- [X] T031 [P] [US3] Create `tests/fixtures/html_cases.json`: a list of at least 25 objects `{"name", "input", "output"}`.
  - **Cases to cover**:
    - each allowed tag (`p`, `h2`, `h3`, `ul`, `ol`, `li`, `strong`, `em`, `mark`, `a`, `br`);
    - `script`, `style`, `iframe`, `img` and `svg` removed;
    - `on*` and `style` attributes removed;
    - `href` with `javascript:`, `data:` and `vbscript:` removed, keeping the text;
    - `http`, `https`, `mailto` and `file` kept;
    - Google Docs paste: `<b style="font-weight:normal">` wrapper, `span` with `background-color` becoming `mark`, and colors and fonts dropped;
    - nested lists, `h1` and `h4`, `div` inside `div`, empty text.
  - **Value of `output`**: what the prototype's `sanitizeHTML` produces. Generate it by opening `specs/semana.html` in Chromium and running the function; check it against FR-035 and FR-036.
- [X] T032 [US3] Create `tests/api/test_sanitize.py` over `tests/fixtures/html_cases.json`, which depends on T031. For each case:
  - (a) `clean(output) == output`: the client's output is a fixed point of the server (R11);
  - (b) `clean(input)` contains no tag outside the list, no attribute other than `href` on `a`, and no `href` with a scheme outside `http`, `https`, `mailto` and `file`. Check with `html.parser`;
  - (c) `clean(clean(x)) == clean(x)`.
- [X] T033 [P] [US3] Create `tests/e2e/test_pure.py`, with Chromium against the `server` fixture, loading `await import('/js/pure.js')` through `page.evaluate`:
  - **Sanitizing**: `sanitizeHTML(input) === output` for each case in `html_cases.json`.
  - **Links and paths** (FR-037), with `parseLink`, `nativePath`, `linkLabel` and `autoLink`:
    - `example.com.br/x` becomes an https address;
    - `ana@example.com` becomes mailto;
    - `"C:\Users\ana\Final contract.pdf"`, with quotes, a space and an accent, becomes `file:///C:/…` and comes back the same through `nativePath`;
    - `\\server\folder\a.docx` becomes `file://server/folder/a.docx`;
    - `/home/ana/a.txt` becomes `file:///home/ana/a.txt`;
    - `~/a.txt` is refused and asks for the full path;
    - `linkLabel` shows the shortened address or the file name.
  - **Expected values**: capture the functions' current behavior and check it against FR-037.
- [X] T034 [P] [US3] In `tests/api/test_ops.py`, add:
  - **Text with revision** (R7):
    - `task.title` with `base_rev` 0 gives `ok` with `rev` 1.
    - Resending the same value with `base_rev` 0 gives `ok`.
    - Another value with `base_rev` 0 gives `conflict` with the current `value` and `rev`.
    - Two clients, one editing `title` and the other `notes` of the same task, cause no conflict (FR-061).
  - **Sanitizing on save**: `task.notes` saves without `<script>`.
  - **Limits**:
    - a 501-character title gives `invalid`;
    - notes over 1,000,000 bytes give `invalid`;
    - an empty or whitespace-only `subtask.text` gives `invalid` (FR-039).
  - **Subtasks**:
    - `subtask.create` is idempotent and accepts `created_at` and `done_at` to undo a deletion.
    - `subtask.done` sets and clears `done_at` and touches the task.
  - **Cascade**: deleting the task erases its subtasks and log.
- [X] T035 [P] [US3] In `tests/api/test_isolation.py`, add to `CASES` the operations `task.title`, `task.notes`, `subtask.create` (A's `task_id`), `subtask.text`, `subtask.done` and `subtask.delete`.

### Implementation for User Story 3

- [X] T036 [US3] Create `src/semana/sanitize.py` with `clean(html: str) -> str`. It uses `nh3.clean(html, tags={"p","h2","h3","ul","ol","li","strong","em","mark","a","br"}, attributes={"a": {"href"}}, url_schemes={"http","https","mailto","file"}, link_rel=None, strip_comments=True)`, with `clean_content_tags` containing `script` and `style`. Adjust the parameters until T032 passes, without changing the expected outputs.
- [X] T037 [US3] In `src/semana/ops.py`, create the helper function `write_text(con, table, column, key, account_id, value, base_rev)` with the R7 rule:
  - row does not exist: `not_found`;
  - `base_rev` equal to the current revision: saves, increments the revision and responds `ok` with `rev`;
  - value equal to the current one: `ok` with the current `rev`;
  - otherwise: `conflict` with `value` and `rev`.

  Handlers:
  - **`task.title`**: `value` with the constraint "plain text, up to 500 characters" (strip) and `base_rev: int`. Touches the task.
  - **`task.notes`**: `value` goes through `clean()` before comparing and saving, with the constraint "up to 1 MB", and carries `base_rev`. Touches the task.
  - **`subtask.create`**: `id`, `task_id` (the account's), `text` with the constraint "plain text, 1–500 characters, never empty", `created_at?` and `done_at?`. Uses `ON CONFLICT DO NOTHING`. Touches the task.
  - **`subtask.text`**: `id`, `value` (1–500 characters) and `base_rev`. Touches the task.
  - **`subtask.done`**: `id` and `done: bool`, which fills in or clears `done_at`. Touches the task.
  - **`subtask.delete`**: `id`. Touches the task, if it still exists.
- [X] T038 [US3] In `src/semana/static/js/app.js`, wire the document to the operations:
  - `saveTitle` (line 1289) produces `task.title`, with `base_rev: t.rev.title`.
  - `saveNotes` (line 1276) with `ed.kind !== 'week'` produces `task.notes`, with `base_rev: t.rev.notes`.
  - `addSubtask` (line 1550) produces `subtask.create`.
  - Editing a subtask in place produces `subtask.text`.
  - `setDone` (line 1549) produces `subtask.done`, including through the `sub-done` and `sub-reopen` handlers.
  - `deleteSub` (line 1557) produces `subtask.delete`. The toast's undo produces `subtask.create` with the same `id`, `text`, `created_at` and `done_at`.
  - The confirmed trash can produces `task.delete` (FR-034).
  - `data.onRev` updates `t.rev` and `sub.rev` in the in-memory state.
- [X] T039 [US3] In `src/semana/static/js/app.js`, create the conflict notice (FR-061, R7), handled in `data.onConflict(op, value, rev)`:
  - **Open task**: the notice shows up inside the document, right above the field and with no modal, with the text "This text was changed on another device after you opened it." and two buttons:
    - **"Keep my version"**: stores the server's `rev` in the local state and enqueues the local value again;
    - **"Use the other version"**: replaces the field's content with the server's `value` and stores the `rev`.
  - **Discarded version**: stays in a read-only block with a "Copy" button until the person closes the notice with ×.
  - **Closed task**: a "Conflict in <title>" toast with a "View" action opens the task with the notice.
  - **Week notes**: the same notice shows up in the overview.

**Checkpoint**: T032 to T035 pass and the US3 independent test works manually, including the conflict with two windows.

---

## Phase 6: User Story 4 - Weekly rollover (Priority: P2)

**Goal**: server-side rollover, idempotent, with read-only snapshots.

**Independent Test**: with open and done tasks, simulate the passing of one and of several weeks and check carry-overs, the counter, the log and the snapshots.

### Tests for User Story 4 ⚠️

- [X] T040 [P] [US4] Create `tests/api/test_rollover.py`, using the `clock` fixture and an account in `America/Sao_Paulo`:
  - (a) **Carry-over**:
    - Initial state: open tasks at 0% and 40%, one important and one with subtasks, notes and log; one done; one task already planned for next week.
    - After `set("2026-11-02T03:00:00Z")`, which is Monday 00:00 in São Paulo, the open tasks show up at the top of week `2026-11-02`, in the original order, followed by the planned task.
    - The carried-over tasks have `weeks_open` 2 and the log entry "Carried over from the week of 2026-10-26". Id, fields, subtasks and `created_at` are preserved and `updated_at` does not change.
    - The done task stays in `2026-10-26`, and that week's snapshot contains all the tasks.
  - (b) **Time zone**: at `2026-11-02T02:59:00Z` (Sunday 23:59 in São Paulo) the rollover has not happened yet.
  - (c) **Absence**: absences of 2 and 5 weeks process each week once, with the counter adding N and one snapshot per week with tasks.
  - (d) **Idempotency**: two consecutive calls to `/api/start` duplicate nothing. Two threads, each with its own `TestClient`, calling at the same time do not either (SC-006).
  - (e) **Future**: tasks from future weeks are never pulled forward.
  - (f) **Snapshot**: deleting a task after the rollover does not change the snapshot.
  - (g) **Past**: `GET /api/week` for a closed week returns `state` `past` and the snapshot's tasks for that project.
  - (h) **Late creation**: `task.create` for the closed week, sent after the rollover, saves in the current week.

### Implementation for User Story 4

- [X] T041 [US4] Create `src/semana/rollover.py` with `apply(con, account_id)`, implementing the R12 algorithm literally inside `transaction(con)`:
  1. Rereads `processed_week` after `BEGIN IMMEDIATE`.
  2. While `add_days(processed_week, 7) < monday(now, timezone)`, with `w = add_days(processed_week, 7)`:
     1. Writes the snapshot of `w` (`INSERT OR IGNORE`), with a list of `task_json(...)` plus `project_id`, only if there are tasks in `w`.
     2. For each project, takes the tasks of `w` with progress below 100, in order (k tasks).
     3. Adds k to the `position` of the tasks already in `w + 7` in that project and moves the open ones to `w + 7` with `position` from 1 to k.
     4. Increments `weeks_open` and writes `log_entry` (`kind` `system`, `text` "Carried over from the week of YYYY-MM-DD", with the date `w`), without touching `updated_at`.
     5. Updates `processed_week = w`.

  Call `apply` at the start of `GET /api/start` and of `GET /api/week`, in `src/semana/reads.py`.
- [X] T042 [US4] In `src/semana/static/js/app.js`, adapt the client-side rollover:
  - **New `tick()`** (line 1997), called every 60 s and on a visible `visibilitychange`: computes the Monday of `Date.now() + offset` in `account.timezone` with `Intl.DateTimeFormat`. If it differs from `S.week`:
    - calls `flushEdits()`;
    - reloads `data.start()` and the displayed week;
    - if the person was on the week that rolled over, moves to the new one;
    - shows the notice "New week. Pending tasks were carried over." (FR-047).
  - **Read-only**: weeks with `state` `past` use `S.snapshots` and `readOnly()`. The document bar shows only the read-only notice and the × (FR-031).
  - **Labels**: PAST and PLANNING follow the `state` (FR-014).

**Checkpoint**: T040 passes and, with `SEMANA_NOW` (see the [quickstart](quickstart.md)), US4 works manually.

---

## Phase 7: User Story 5 - Lose nothing when the connection drops (Priority: P2)

**Goal**: edit offline, including reopening the tab, and send everything on reconnect.

**Independent Test**: with a task open, turn off the network, edit title, notes and subtasks, close and reopen the tab, turn the network back on and check on another device.

### Tests for User Story 5 ⚠️

- [X] T043 [P] [US5] Create `tests/e2e/test_offline.py` with Playwright against the `server` fixture:
  - (a) **Outage with the tab reopened** (SC-004):
    1. Sign up the account, create a task and open it.
    2. `context.set_offline(True)`.
    3. Edit the title and the notes and create a subtask and a new task. The footer must contain "Offline" and the count.
    4. Close the page and open another one in the same context, still offline. The app loads through the service worker and shows the edits.
    5. `set_offline(False)`. The footer must show "Saved" within 10 s.
    6. In a second context, log in to the same account and see everything.
  - (b) **Log out with pending changes**: the discard confirmation appears (FR-058).
  - (c) **Expired session**:
    - With pending changes, delete the session in the database (`DELETE FROM session`) and reconnect.
    - The login screen appears with the notice. Logging in to the same account sends the pending changes (FR-059).
    - Logging in with another account sends nothing to it (FR-058).
  - (d) **Week not loaded**: offline, opening a week never loaded shows "You need a connection to open this week." (FR-057).

### Implementation for User Story 5

- [X] T044 [P] [US5] Create `src/semana/static/sw.js` (R5):
  - **`install`**: opens the `semana-static` cache, stores `['/', '/app.css', '/js/app.js', '/js/pure.js', '/js/data.js']` and calls `skipWaiting()`.
  - **`activate`**: `clients.claim()`.
  - **`fetch`**: only for same-origin `GET`s whose path does not start with `/api`. Tries the network first and, on success, stores a copy. If the network fails, uses `caches.match`. Navigations without a cache fall back to `'/'`.

  In `src/semana/static/js/app.js`, register it with `navigator.serviceWorker?.register('/sw.js').catch(() => {})`. In `src/semana/app.py`, serve `/sw.js` with `Cache-Control: no-cache`.
- [X] T045 [US5] In `src/semana/static/js/app.js`, handle offline operation:
  - **Opening without a network**: if `data.start()` fails because of the network, use the cache of the account in `localStorage['semana-account']`. Without a cache, the login screen shows "No connection. Connect to log in."
  - **Week not loaded**: navigating offline to a week or project outside the cache (`offline`) shows the notice "You need a connection to open this week." and keeps the current view (FR-057).
  - **Hiding the tab**: on a hidden `visibilitychange` and on `pagehide`, call `flushEdits()` and `data.send()` (FR-033).
  - **Reloading what changed on another device**: on a visible `visibilitychange` and on each navigation, reload the view from the server **only if the queue is empty**, so as not to overwrite local pending changes (FR-060). Mark with `// ponytail: no reload unless the queue is empty; merge per field if that bothers anyone`.
- [X] T046 [US5] In `src/semana/static/js/app.js`, handle the expired session with `data.onSession`:
  - Shows the login screen with the notice "Your session expired. Log in again to send N changes.", without erasing the cache or the queue.
  - After logging in: if `account.id` is the same as the queue's, calls `data.send()`. If it is another account, it neither shows nor sends the earlier pending changes (FR-058, FR-059).

**Checkpoint**: T043 passes.

---

## Phase 8: User Story 6 - Overview and week notes (Priority: P3)

**Goal**: panel with no task open showing week notes, pending subtasks and "Worth picking up".

**Independent Test**: write week notes, create subtasks in several tasks, leave a task without updates for 72 hours and check the overview.

### Tests for User Story 6 ⚠️

- [X] T047 [P] [US6] Add the `week.notes` tests:
  - In `tests/api/test_ops.py`:
    - with no row, `base_rev` 0 gives `ok` with `rev` 1;
    - conflict with an outdated `base_rev`;
    - `<script>` removed;
    - an empty `value` responds `ok`, and `GET /api/week` returns `{"html": "", "rev": n}`;
    - a `week` that is not a Monday gives `invalid`.
  - In `tests/api/test_isolation.py`: the `week.notes` case with A's `project_id`.

### Implementation for User Story 6

- [X] T048 [US6] In `src/semana/ops.py`, create the `week.notes` handler:
  - Fields: `project_id` (the account's), `week` (a Monday), `value` (passed through `clean()`, with the constraint "up to 1 MB") and `base_rev`.
  - If the row does not exist, it is treated as `rev` 0: with `base_rev` 0, inserts with `rev` 1; otherwise, `conflict` with `{"value": "", "rev": 0}`.
  - If the row exists, it applies `write_text`. An empty value is saved as `''` and keeps the revision (FR-052).
- [X] T049 [US6] In `src/semana/static/js/app.js`, adapt `dashboardHTML` (line 1159) to FR-050:
  - **Week notes**: with `saveNotes` on `ed.kind === 'week'`, they produce `week.notes` with `base_rev: S.notesRev[key]`, which `data.onRev` updates.
  - **Pending subtasks**: those of the open tasks, in list order, with the `dash-done` checkbox, which produces `subtask.done`, and the `open-task` link.
  - **"Worth picking up"**: open tasks with `lastActivity <= Date.now() + offset - 72h`, except in future weeks (FR-051).
  - **Remove**: "On the agenda" and any reference to events.
  - **Past**: in past weeks, everything is read-only.

**Checkpoint**: T047 passes and the US6 independent test works with `SEMANA_NOW` 72 h ahead.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T050 [P] Create `tests/e2e/test_keyboard_mobile.py` (SC-008), with a 360×740 viewport and `has_touch=True`. The whole flow is done with the keyboard alone:
  1. Sign-up.
  2. "+ New task" and type the title.
  3. Enter moves to the notes.
  4. Esc closes the task.
  5. Alt+↓ reorders.
  6. → adjusts the progress.
  7. Open the profile menu and choose "Log out".

  Also assert that `document.scrollingElement.scrollWidth <= 360`, that is, no horizontal scrolling.
- [X] T051 [P] Create `tests/load.py` (SC-007), an `httpx.AsyncClient` script with the arguments `--url`, `--users` and `--minutes`:
  - creates N accounts;
  - each one runs `GET /api/week` and a `task.title` every 3 s;
  - prints the p95 of each route and exits with code 1 if the `GET` p95 goes over 500 ms or the `POST /api/ops` p95 goes over 1 s.

  It must not be collected by pytest: the file name does not start with `test_`.
- [X] T052 Run `uv run ruff check src tests` and `uv run pytest` and walk through the whole manual validation in [quickstart.md](quickstart.md), US1 to US6, fixing the discrepancies found.

**Outside this feature** (decision of 2026-10-27: for now the app only runs locally): `deploy/` (Caddy, systemd), `src/semana/backup.py` and the choice of SMTP provider. In local mode, the password recovery link shows up in the log (T021).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (phase 1)**: no dependencies.
- **Foundational (phase 2)**: depends on phase 1 and blocks every story.
- **US1 (phase 3)**: depends on phase 2.
- **US2 (phase 4)**: depends on US1, which has the account and the isolation test.
- **US3 (phase 5)**: depends on US2, because it needs tasks to document.
- **US4 (phase 6)**: depends on US2. It can run in parallel with US3.
- **US5 (phase 7)**: depends on US3, because it needs text edits to test the queue.
- **US6 (phase 8)**: depends on US3, because it reuses the editor and `write_text`.
- **Polish (phase 9)**: depends on every story.

```text
Setup → Foundational → US1 → US2 ─┬→ US3 ─┬→ US5
                                  │       └→ US6
                                  └→ US4
                                        → Polish
```

### Within Each User Story

- Tests come first and must fail before the implementation.
- On the server, handlers come before wiring them in the client.
- Each story ends at its checkpoint before the next one.

### Parallel Opportunities

- **Setup**: T002, T003 and T004 run together, after T001. T005 depends on T004.
- **Foundational**:
  - T008, T014 and T015 run in parallel with the rest.
  - T006 → T007 → T009 → T010 → T011 → T012 → T013 run in sequence.
  - T016 and T017 depend on T015 and T005.
- **US1**: T018, T019, T021 and T024 run together.
- **US2**: T027 and T028 run together.
- **US3**: T031, T034 and T035 run together. T032 and T033 run together after T031.
- **US4 and US3**: different teams can take them in parallel after US2. Only T042 and T038 touch the same `app.js` file.
- **US5**: T043 and T044 run together.
- **Polish**: T050 and T051 run together.

---

## Parallel Example: User Story 3

```bash
# Tests that do not depend on each other:
Task: "T031 Create tests/fixtures/html_cases.json"
Task: "T034 Text and subtask cases in tests/api/test_ops.py"
Task: "T035 US3 isolation cases in tests/api/test_isolation.py"

# After T031:
Task: "T032 tests/api/test_sanitize.py"
Task: "T033 tests/e2e/test_pure.py"
```

---

## Implementation Strategy

### MVP First

1. Setup and Foundational.
2. US1, US2 and US3: the three P1 stories, which only together make a usable product (account, list and document).
3. **Stop and validate** with the quickstart, US1 to US3.

### Incremental Delivery

1. MVP (US1 to US3), validated.
2. US4 (rollover). From here on the app can be used for more than a week.
3. US5 (connection drop). From here on it can be trusted for daily use.
4. US6 (overview).
5. Polish: SC-007 and SC-008.

---

## Notes

- **[P]**: different files and no pending dependency.
- **Isolation**: every new operation needs a case in `tests/api/test_isolation.py`, or T019 fails. This is intentional.
- **Prototype**: `specs/semana.html` is still the behavior reference. When adapting one of its functions, change only what the API needs.
- **Commits**: there is no git repository in this folder. Initializing one (`git init`) before implementation allows one commit per task or group of tasks.
