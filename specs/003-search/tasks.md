---

description: "Implementation tasks for feature 003: search"
---

# Tasks: Search

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md)

**Tests**: required (constitution VI names search: accents and ordering), plus isolation.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

Nothing to prepare (project from 001).

---

## Phase 2: Foundational

- [X] T001 In `src/semana/static/js/pure.js`, recover from the prototype (`specs/semana.html`) and export: `textOf` and `fold` (lines 879–881); and, from lines 1633–1671, pure versions of `rankSearch`, `markTerms` and `snippetOf`: `rankSearch(items, q, currentWeek)` takes the list and the current week instead of reading `search.items` and `S.week`; `markTerms` and `snippetOf` with no logic change. Add `searchItems(tasks, notes)`, a pure version of the prototype's `searchItems` (line 1633) that builds the items from tasks in the prototype format and a `{"week|project": html}` object.

---

## Phase 3: User Story 1 - Find anything written (Priority: P1) 🎯 MVP

**Goal**: Ctrl+Space, the prototype's ranking over all of the account's content, opening in the right place.

**Independent Test**: content across several weeks and projects; search with and without accents, capitals, two words; open each kind of result.

### Tests for User Story 1 ⚠️

- [X] T002 [P] [US1] Create `tests/e2e/test_search_box.py::test_ranking` (via `page.evaluate` on `pure.js`, like `tests/e2e/test_pure.py`): items titled "Café with Joana", "Café", "Notes from the café", a task with "café" only in its notes, a done "Old café" and week notes with "café"; assert that "cafe", "CAFÉ" and "café" give the same list; that "Café" (equal title) comes before "Café with Joana" (start), which comes before "Notes from the café" (middle), before the content results; that, with the same score, current week > future > past and open > done; that "cafe joana" brings only the first; that an empty field brings up to 8 open tasks by descending `updated_at`; and that `snippetOf` returns a snippet with `<mark>` for a term only in the content.
- [X] T003 [P] [US1] Create `tests/api/test_search_index.py`: `GET /api/search` returns tasks from every week and project with `title`, `notes`, `subtasks` (including done ones), `progress`, `important`, `due`, `updated_at`, `week`, `project_id`; returns week notes only when `html` is not empty; 401 with no session.
- [X] T004 [P] [US1] In `tests/api/test_isolation.py`, create `test_search_isolated`: with A's data from the `accounts` fixture, B's `GET /api/search` returns `{"tasks": [], "notes": []}` (SC-004).
- [X] T005 [P] [US1] In `tests/e2e/test_search_box.py`, create `test_flow`: sign up; create "Café with Joana" in the current week; go to the previous week, create a task with "résumé" in its notes; go back to the current week; Ctrl+Space opens `#search` with the field focused; type "resume": the first result has a snippet with `mark`; Enter goes to the previous week, opens the task and the document selection contains "résumé"; with the cursor in the notes, Ctrl+Space and Esc give focus back to `#notes`; Ctrl+Space twice closes.

### Implementation for User Story 1

- [X] T006 [US1] In `src/semana/reads.py`, create `GET /api/search` per [contracts/api.md](contracts/api.md): one query for tasks and one for subtasks (`GROUP BY task_id` or grouping in Python), and notes with `html <> ''`, all with `account_id = ?`.
- [X] T007 [P] [US1] In `src/semana/static/js/data.js`, create `search()` with cache under the key `search` (same `withCache` as `week` and `agenda`), but which, with no network and no cache, returns `{tasks: [], notes: [], offline: true}` instead of throwing; with cache and no network, returns the cache with `offline: true`.
- [X] T008 [US1] In `src/semana/static/js/app.js`, recover the search box from the prototype: `drawResults`, `openSearch`, `closeSearch`, `chooseResult`, `revealIn`, `weekLabel` (lines 1672–1727) and the handlers for `mousedown` (`.so`), `mousemove`, click (outside the box closes; `.so` opens), `input` on `#search-input` and the `keydown` for Ctrl+Space/arrows/Enter/Esc/Tab (see lines 1733–1747 and 1890–1899 of the prototype). Icons `search` and `notes` (lines 987–988). Changes:
  - `openSearch` saves edits (`flushEdits`), builds items with `searchItems` from the index (`data.search()`) converted to the prototype format, laying `S.tasks`, `S.snapshots` and `S.notes` over it by id/key, and redraws when the index arrives; the newest index is fetched in the background on every open.
  - Offline (`offline`), the box shows at the top of the list: "Offline: results only from what was already opened on this device." (FR-021).
  - `chooseResult`: for a task, `screen='tasks'`, `await goTo(it.week, it.projectId)`, `pane={id}`, `drawList(); drawDetail()`; for notes, `goTo` and the overview; then `revealIn(ed.notes, terms)`.
  - `rankSearch(items, q, S.week)` and the due date on the result via `dueShort` (002).
  - Ctrl+Space only works with a signed-in account (`S`).
- [X] T009 [US1] In `headerHTML` (`src/semana/static/js/app.js`), put back the prototype's `<span class="search-hint">` hint ("Search" + `<kbd>Ctrl</kbd><kbd>Space</kbd>`) before the profile menu.

**Checkpoint**: T002–T005 pass.

---

## Phase 4: User Story 2 - Search on mobile (Priority: P2)

- [X] T010 [P] [US2] In `tests/e2e/test_search_box.py`, create `test_search_button` (originally named `test_magnifier_on_mobile`) in a 360×740 context with `has_touch`: the magnifier (`button` "Search") is visible and `.search-hint` is not; tapping the magnifier opens the box; searching and tapping a result opens the task; no sideways scrolling. And on desktop without touch (1280×800): the magnifier does not show and the hint does.
- [X] T011 [US2] In `src/semana/static/js/app.js`, add to the header `btn('search', icons.search, '', 'icon-btn search-btn', t('search.button'))` and `case 'search': openSearch(); return;`. In `src/semana/static/app.css`, `.search-btn{display:none}` and, in `@media(hover:none),(pointer:coarse)` and `@media(max-width:760px)`, `.search-btn{display:inline-flex}` (R3). (Later the magnifier was made visible on every screen, since some browsers keep Ctrl+Space for themselves; `.search-hint` and the `display:none` rule were removed and `test_search_button` checks the button on desktop and on a phone.)

---

## Phase 5: User Story 3 - Offline and only in your own content (Priority: P2)

- [X] T012 [P] [US3] In `tests/e2e/test_search_box.py`, create `test_search_offline`: sign up, create "Contract" and wait for "Saved"; `sw_ready`; `set_offline(True)`; change the title to "New contract" (pending); Ctrl+Space, "new": "New contract" shows along with the connection notice (FR-016, FR-021).

Implementation covered by T007 and T008 (cached index, local overlay and notice). Isolation covered by T004 and T006.

---

## Phase 6: Polish

- [X] T013 Run `uv run ruff check src tests` and `SEMANA_CHROMIUM=/usr/bin/chromium uv run pytest` (001–003) and the 003 quickstart.

---

## Dependencies & Execution Order

- T001 before everything on the client; T006 before T005/T012 run.
- US1 → US2 (the magnifier opens the US1 box) and US3 (tests what T007/T008 do).
- [P]: T002–T005 together; T007 with T006; T010 and T012 together.

## Parallel Example: User Story 1

```bash
Task: "T002 test_ranking in tests/e2e/test_search_box.py"
Task: "T003 tests/api/test_search_index.py"
Task: "T004 test_search_isolated in tests/api/test_isolation.py"
```

## Implementation Strategy

MVP = US1 (shortcut and ranking over the whole account). Then the magnifier (US2) and the offline test (US3).
