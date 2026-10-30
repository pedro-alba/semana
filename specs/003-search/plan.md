# Implementation Plan: Search

**Branch**: `003-search` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-search/spec.md`

## Summary

Bring back the prototype's search (Ctrl+Space), now over all of the account's content. The server gains a read route, `GET /api/search`, with the account's index; the client keeps that index, lays what it has in memory over it and runs the prototype's ranking locally, which works offline and includes pending changes ([research R1](research.md)). On touch screens, a magnifier in the header opens the same box.

## Technical Context

**Language/Version**: Python 3.12; JavaScript ES2022 with no build (same as 001)

**Primary Dependencies**: none new

**Storage**: no schema change; index in the client's IndexedDB cache (key `search`)

**Testing**: pytest (API) and pytest-playwright (ranking in `pure.js` via `page.evaluate`, box flow)

**Target Platform**: local, for now

**Project Type**: web application (same process)

**Performance Goals**: results ≤ 300 ms after typing stops with ~1,500 tasks (SC-001)

**Constraints**: offline, local search with a notice; keyboard and 360 px with touch

**Scale/Scope**: 1 route, ~150 lines of client code recovered from the prototype

## Constitution Check

| Principle | How the plan complies | Status |
| --- | --- | --- |
| I. Fewer controls | Search off screen, by shortcut; the magnifier only shows where there is no shortcut (owner's decision) | ✅ |
| II. The week is the unit | Results show the week and open in it | ✅ |
| III. Nothing gets lost | Opening search saves what was being edited; results include pending changes | ✅ |
| IV. Data belongs to the account only | Route filters by `account_id`; isolation test; snippets go through `esc`/`markTerms` | ✅ |
| V. Simplicity | No dependency, table or database index; reuses the prototype's ranking | ✅ |
| VI. Tests | Accents, ordering, snippets, isolation and flow | ✅ |

**Re-check after Phase 1**: no violations.

## Project Structure

```text
specs/003-search/{plan,research,data-model,quickstart}.md, contracts/api.md, tasks.md
src/semana/reads.py              # GET /api/search
src/semana/static/js/pure.js     # fold, textOf, rankSearch, markTerms, snippetOf
src/semana/static/js/data.js     # search(): index with cache
src/semana/static/js/app.js      # search box, magnifier, shortcut, opening
tests/api/test_search_index.py
tests/e2e/test_search_box.py
```

**Structure Decision**: no new code files besides the tests.

## Complexity Tracking

No additions.
