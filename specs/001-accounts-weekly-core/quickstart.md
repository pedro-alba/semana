# Quickstart: Accounts and weekly core

Guide to run the app and validate the feature end to end. The routes are in [contracts/api.md](contracts/api.md), the data in [data-model.md](data-model.md) and the technical decisions in [research.md](research.md).

## Prerequisites

- Linux or macOS with [uv](https://docs.astral.sh/uv/). uv installs Python 3.12 on its own.
- Playwright's Chromium, for the browser tests.

## Set up and run

```sh
uv sync
uv run playwright install chromium
SEMANA_DB=./dev.sqlite3 SEMANA_SECURE_COOKIE=0 SEMANA_BASE_URL=http://localhost:8000 \
  uv run uvicorn semana.app:app --reload
```

Open `http://localhost:8000`. Migrations run at startup. Without SMTP configured, the password recovery link shows up in the server log.

| Variable | Use | Default |
| --- | --- | --- |
| `SEMANA_DB` | path to the SQLite file | `semana.sqlite3` |
| `SEMANA_BASE_URL` | origin used in the recovery link | required in production |
| `SEMANA_SECURE_COOKIE` | `0` only in local development without HTTPS | `1` |
| `SEMANA_SMTP_HOST`, `_PORT`, `_USER`, `_PASSWORD`, `_FROM` | e-mail sending (R10) | no host: the link goes to the log |

## Automated tests

```sh
uv run pytest                 # everything
uv run pytest tests/api       # server: isolation, rollover, ops, accounts, sanitizing
uv run pytest tests/e2e       # browser: offline queue, keyboard, 360 px, links, pasting
```

Each subtle rule of the constitution (principle VI) has its test:

| Rule | The test proves |
| --- | --- |
| Isolation (SC-005) | for each operation type and each `GET`, account B gets `not_found`/404 on account A's data and nothing changes |
| Rollover (SC-006) | absences of 1, 2 and 5 weeks and two simultaneous requests: no duplication or loss, with correct order, counter and log |
| Idempotency and conflict (FR-061) | resending a batch changes nothing; concurrent edits to the same field return `conflict`; different fields do not |
| Sanitizing | `tests/fixtures/html_cases.json`: the client's `sanitizeHTML` produces the expected output; that output passes through `nh3` unchanged; no input lets through a forbidden tag, attribute or scheme |
| Links and paths | Windows paths (including quoted ones), network paths (`\\server\folder`), macOS/Linux and `~` (FR-037) |
| Sending after an outage (SC-004) | offline changes, with the tab closed and reopened, reach a second browser context |

## Manual validation per story

Use two browsers (or a private window) as "device 1" and "device 2".

1. **US1, account:**
   1. Sign up `a@test.com`: you go straight into Personal, in the current week, with the overview.
   2. Create a task.
   3. On device 2, log in with the same account: the task is there.
   4. Sign up `b@test.com` on device 2: nothing from A shows up.
   5. Copy the `GET /api/week?project=<A's id>…` from device 1's network tab and open it in B's session: the response is 404.
   6. Request password recovery for A and use the link from the log: A's other sessions drop.
   7. Delete account B: the e-mail accepts sign-up again.
2. **US2, week:** create tasks in the current week and the next one. Drag the progress to 100% and confirm the task goes to the end of Done. Reorder with the mouse, with touch (DevTools at 360 px) and with Alt + arrow, then reload: the order persists.
3. **US3, document:**
   1. Format the text with the bar and with the shortcuts.
   2. Paste a passage from Google Docs with highlights and colors: highlights and links stay, colors and fonts go.
   3. Create and complete subtasks, then undo and reopen one from the log.
   4. Paste `"C:\Users\ana\contract.pdf"`: the popover offers "Copy path".
   5. Reload: everything persists.
4. **US4, rollover:** with the development server, move the clock forward (variable `SEMANA_NOW=2026-11-02T03:00:00Z`, used only in development and tests) and reload:
   - the open tasks go to the top of the new week with "↪ week 2";
   - the done tasks stay in the previous week;
   - the previous week opens read-only.
5. **US5, offline:**
   1. In DevTools › Network › Offline, edit the title and the notes and create a subtask: the footer shows "offline" and the number of pending changes.
   2. Close the tab, reopen it still offline and confirm the edit is still there.
   3. Bring the connection back: the footer changes to "saved" and device 2 shows the changes.
   4. Edit the same title on both devices: the second one to save sees the conflict notice and chooses the version.
   5. With pending changes, try to log out: the discard warning appears.
6. **US6, overview:** write week notes and create subtasks in two tasks. Move the clock 72 hours ahead, as in US4: the task shows up in "Worth picking up".

## Load (SC-007)

```sh
uv run python tests/load.py --url http://localhost:8000 --users 1000 --minutes 2
```

The script creates 1,000 accounts and, for each one, opens the week and saves a text every 3 s. It prints the p95 of `GET /api/week` and of `POST /api/ops`. It passes if the `GET` p95 stays below 500 ms and the `POST` p95 below 1 s, which leaves room for SC-002 (2 s) and SC-003 (3 s), on a 1 vCPU, 1 GB VPS.

## Deploy (summary, postponed)

For now the app only runs locally. These files wait until the VPS and the e-mail provider are chosen.

- `deploy/semana.service`: uvicorn with 2 workers, `--proxy-headers`, unprivileged user.
- `deploy/Caddyfile`: automatic HTTPS, proxy to uvicorn, HSTS and access log.
- `deploy/semana-backup.timer`: runs `python -m semana.backup /var/backups/semana` once a day and keeps 30 days of copies.
