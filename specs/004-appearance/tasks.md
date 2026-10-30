---

description: "Implementation tasks for feature 004: appearance"
---

# Tasks: Appearance

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md)

**Tests**: required (constitution VI and isolation cases for every new operation).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

Nothing to prepare (project from 001).

---

## Phase 2: Foundational

- [X] T001 Create `src/semana/migrations/003_appearance.sql` with `ALTER TABLE account ADD COLUMN appearance TEXT NOT NULL DEFAULT '{}';`. (Now part of `migrations/001_initial.sql`.)
- [X] T002 In `src/semana/accounts.py`, `account_json` now returns `"appearance": json.loads(c["appearance"])`; `POST /api/account` returns `{"account": account_json(...)}` reading the newly created row, instead of the hand-built dictionary.
- [X] T003 Create `src/semana/static/js/appearance.js` (classic script, not a module) per [R1](research.md) and [data-model](data-model.md):
  - `VALUES = {theme:['graphite','paper','ink'], mode:['light','dark','system'], font:['theme','mono','sans','serif'], palette:['classic','sunset','lavender','moss','traffic','neutral']}` and `DEFAULT = {theme:'graphite', mode:'dark', font:'theme', palette:'classic'}`;
  - `normalize(p)`: a missing key or a value outside `VALUES` becomes the default;
  - `apply(p)`: normalizes, sets `data-theme`, `data-mode-pref`, `data-font`, `data-palette` and `data-mode` (from `matchMedia('(prefers-color-scheme: dark)')` when `mode==='system'`) on `<html>`, updates `data-mode` on the `.swatch` elements and writes `localStorage['semana-appearance']` (inside `try`);
  - `current()` reads the attributes from `<html>` and returns the object; `forget()` removes the key from `localStorage` and applies `DEFAULT`;
  - a `change` listener on the `matchMedia` reapplies `data-mode` when `mode==='system'` (FR-003);
  - on load, applies the `localStorage` copy (or the default) and exposes `window.appearance = {VALUES, DEFAULT, normalize, apply, current, forget}`.
- [X] T004 In `src/semana/static/index.html`, `terms.html` and `privacy.html`, put `<script src="/js/appearance.js"></script>` in the `<head>`, before the `<link rel="stylesheet">`. In `src/semana/static/sw.js`, add `'/js/appearance.js'` to the `addAll` list. (Done without renaming `CACHE`: the service worker goes network-first and its bytes change, so it reinstalls itself.)

---

## Phase 3: User Story 1 - Choose the appearance (Priority: P1) 🎯 MVP

**Goal**: the prototype's panel in the profile menu, switching right away and saving to the account.

**Independent Test**: with a task open and the cursor in the notes, change the four choices; the interface changes, the task and the cursor stay, no data changes.

### Tests for User Story 1 ⚠️

- [X] T005 [P] [US1] Create `tests/api/test_appearance_api.py`: a new account returns `"appearance": {}` in `POST /api/account`, `POST /api/login` and `GET /api/start`; `account.appearance` with `{"theme": "paper", "mode": "system", "font": "serif", "palette": "moss"}` returns `ok` and `/api/start` then returns that object; repeating returns `ok`; `"theme": "blue"` returns `{"status": "invalid", "fields": ["theme"]}`; missing `palette` returns `invalid` with `palette`.
- [X] T006 [P] [US1] In `tests/api/test_isolation.py`, add the case `"account.appearance": lambda d: {"theme": "ink", "mode": "light", "font": "mono", "palette": "neutral"}` to `CASES` and its name to `DELETES` (returns `ok`, but only on B's account); in `week_of`, include `client.get("/api/start").json()["account"]` in the tuple, so the test proves A's appearance did not change.
- [X] T007 [P] [US1] Create `tests/e2e/test_appearance_panel.py::test_instant_switch`: sign up; create a task, type "abcdef" in the notes and put the cursor after "abc"; open the profile menu; click Paper, Light, Roboto Mono and Lavender (`[data-pref][data-value]`); assert the `<html>` attributes (`data-theme="paper"`, `data-mode="light"`, `data-font="mono"`, `data-palette="lavender"`), `aria-checked="true"` on the chosen ones, the task still open, the notes still "abcdef" and, after closing the menu with Esc and giving focus back to `#notes`, typing "X" gives "abcXdef"; wait for "Saved" and check `GET /api/start` (via `page.request`) with the chosen appearance. Assert that the menu shows the e-mail, "Log out" and "Delete account" and the text "Preferences for your account. Your data doesn't change.".
- [X] T008 [P] [US1] In `tests/e2e/test_appearance_panel.py`, create `test_contrast`: for each theme × mode × gradient (3 × 2 × 6), via `page.evaluate`, apply with `window.appearance.apply`, read the text and background colors of a card at progress 0, 50 and 100 (create three tasks with those progress values first) and assert contrast ≥ 4.5:1 by the WCAG formula (SC-002). If the card background is transparent, walk up to the first ancestor with a background. If any pair fails, record the combination in the `assert` message.
- [X] T009 [P] [US1] In `tests/e2e/test_appearance_panel.py`, create `test_system_mode`: with `page.emulate_media(color_scheme="light")`, pick System: `data-mode="light"`; `emulate_media(color_scheme="dark")`: `data-mode="dark"` without reloading.

### Implementation for User Story 1

- [X] T010 [US1] In `src/semana/ops.py`, create `account.appearance` per [contracts/api.md](contracts/api.md): model `AccountAppearance` with `theme: Literal["graphite","paper","ink"]`, `mode: Literal["light","dark","system"]`, `font: Literal["theme","mono","sans","serif"]`, `palette: Literal["classic","sunset","lavender","moss","traffic","neutral"]`, all required; the handler writes the `json.dumps` of the four to `account.appearance WHERE id = account["id"]` and returns `OK`.
- [X] T011 [US1] In `src/semana/static/js/app.js`, recover from the prototype (`specs/semana.html`, lines 991–1025) `THEMES`, `MODES`, `FONTS`, `PALETTES` and `prefsHTML`, and the `sun`, `moon` and `monitor` icons (lines 985–986 and nearby) if they do not exist yet. Changes:
  - `pref(k)` reads from `<html>` as in the prototype; `prefsHTML` becomes the content of the default branch of `profileHTML`, between the e-mail and the Log out and Delete account buttons, with the note "Preferences for your account. Your data doesn't change.";
  - `setPref(kind, value)`: builds the object from `appearance.current()` with the key changed (`mode-pref→mode`; `theme`, `font` and `palette` keep their names), calls `appearance.apply`, updates `aria-checked` on the group's buttons, readjusts the editor as in the prototype (`autosize`, `sizeSubs`, `updateBubble` when present, without redrawing the task) and calls `data.enqueue({op:'account.appearance', ...object})`;
  - `case 'pref'` handler with `setPref(el.dataset.pref, el.dataset.value)`; the menu stays open after the click;
  - `#profile-pop` gets the `prefs-pop` class only in the default branch (the width and scrolling styles at 360 px already exist in `app.css`).
- [X] T012 [US1] In `src/semana/static/js/data.js`, add `'account.appearance'` to the `TEXT` set and, in `target`, return `''` for this operation, so that only the last choice stays in the queue.
- [X] T013 [US1] In `start(r)` (`src/semana/static/js/app.js`), call `appearance.apply(r.account.appearance)`.

**Checkpoint**: T005–T009 pass.

---

## Phase 4: User Story 2 - The same appearance on every device (Priority: P2)

**Goal**: the account's appearance applies in every browser, opens without flashing and survives offline.

**Independent Test**: choose in one browser context and sign in from another; reload online and offline.

### Tests for User Story 2 ⚠️

- [X] T014 [P] [US2] In `tests/e2e/test_appearance_panel.py`, create `test_other_device`: sign up in context 1, pick Ink, Light, Serif and Moss, wait for "Saved"; in a new context 2, sign in to the same account: the four `<html>` attributes match; in context 2, pick Graphite and wait for "Saved"; in context 1, fire `visibilitychange` (hide and show the page, as `tests/e2e/test_offline.py` does if there is already a helper for it; otherwise a `page.evaluate` that redefines `document.hidden` and dispatches the event): `data-theme="graphite"`.
- [X] T015 [P] [US2] In `tests/e2e/test_appearance_panel.py`, create `test_first_paint`: after picking Paper and "Saved", register with `page.add_init_script` a `MutationObserver` that stores in `window.__themeOnBody` the `<html>` `data-theme` at the moment `document.body` appears; reload: `__themeOnBody === 'paper'`. Repeat with `sw_ready` and `set_offline(True)`.
- [X] T016 [P] [US2] In `tests/e2e/test_appearance_panel.py`, create `test_pending_offline`: sign up, `sw_ready`, `set_offline(True)`, pick Ink, reload: `data-theme="ink"` (the cached `/api/start` copy does not bring Graphite back); `set_offline(False)`, wait for "Saved": `/api/start` returns `theme: "ink"`.
- [X] T017 [P] [US2] In `tests/e2e/test_appearance_panel.py`, create `test_account_switch`: account A picks Paper; log out: the sign-in screen stays in Paper; sign up B: `data-theme="graphite"` (B's default); delete account B: the screen goes back to the default and `localStorage['semana-appearance']` does not exist.

### Implementation for User Story 2

- [X] T018 [US2] In `start()` in `src/semana/static/js/data.js`, on both paths (server response and cache with no network), if the account's queue has a pending `account.appearance` operation, replace `account.appearance` with the operation's object before returning ([R3](research.md)).
- [X] T019 [US2] In `onReturn()` in `src/semana/static/js/app.js`, before checking pending changes, request `data.start()` and, if it comes back, `appearance.apply(r.account.appearance)` and `drawProfile()` (ignore network failures) ([R4](research.md)).
- [X] T020 [US2] In `deleteAccount` (`src/semana/static/js/app.js`), after a successful delete, call `appearance.forget()`. `logout()` does not touch the appearance.

---

## Phase 5: Polish

- [X] T021 Run `uv run ruff check src tests` and `SEMANA_CHROMIUM=/usr/bin/chromium uv run pytest` (001–004), check at 360 px that the profile menu scrolls inside with no sideways scrolling (quickstart, item 5) and mark the [manual validation](quickstart.md) as pending for the owner.

---

## Dependencies & Execution Order

- T001 → T002 → T010; T003 → T004 → T011–T013.
- Tests T005–T009 together ([P]), before the US1 implementation.
- US2 depends on US1 (the panel and the operation).
- T014–T017 together ([P]); T018–T020 in sequence (T019 and T020 in the same file).

## Parallel Example: User Story 1

```bash
Task: "T005 tests/api/test_appearance_api.py"
Task: "T006 account.appearance case in tests/api/test_isolation.py"
Task: "T007 test_instant_switch in tests/e2e/test_appearance_panel.py"
```

## Implementation Strategy

MVP = US1 (the panel switching right away and saving to the account). Then US2 (other device, first paint, offline, account switch).
