# Research: Search

Same stack as features 001 and 002, with no new dependency.

## R1. Ranking on the client, over an index downloaded from the server

- **Decision**: `GET /api/search` returns an index with all of the account's searchable content (tasks with title, notes, subtask texts, progress, importance, due date and update time; non-empty week notes). The client keeps the index in the cache (`search`) and lays over it the content already in memory (loaded tasks and notes, including pending changes). Ranking and snippets use the prototype's functions (`fold`, `textOf`, `rankSearch`, `markTerms`, `snippetOf`), moved to `pure.js` as pure functions.
- **Rationale**: a single algorithm, the prototype's, works online and offline (FR-021) and already includes local changes (FR-016). Typing makes no request, so SC-001 depends only on downloading the index, done when the box opens and refreshed in the background. The server only filters by `account_id`, which keeps isolation simple (FR-020).
- **Alternatives**: ranking on the server would duplicate the algorithm in Python and would not work offline; SQLite FTS5 does not ignore accents without a custom tokenizer and needs a mirror table kept in sync.
- **Known ceiling**: the index grows with the content (about 1–3 MB for 2 years of typical use). `ponytail:` move ranking to the server, with pre-normalized text, if the index gets too large to download when search opens.

## R2. Opening a result

- **Decision**: opening a result uses the existing navigation (`goTo(week, project)`), opens the task by id (live, or from the snapshot in closed weeks) and calls the prototype's `revealIn` on the notes.
- **Rationale**: reuses the path already tested in features 001 and 002.

## R3. Mobile access

- **Decision**: a magnifier-icon button in the header, visible only with `(hover:none),(pointer:coarse)` or widths up to 760 px; the "Search Ctrl Space" hint uses the opposite rule, already in the prototype's CSS.
- **Rationale**: owner's decision (2026-10-28), solved with CSS alone.
