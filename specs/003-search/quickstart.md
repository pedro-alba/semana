# Quickstart: Search

Running and prerequisites are the same as in [feature 001](../001-accounts-weekly-core/quickstart.md).

## Automated tests

```sh
SEMANA_CHROMIUM=/usr/bin/chromium uv run pytest
```

| Rule | The test proves |
| --- | --- |
| Accents and capitals (SC-003) | "cafe", "CAFÉ" and "café" find "Café"; with two words, all must appear |
| Ordering (FR-012) | equal title > start > middle > content; current week > future > past; done below open with the same score |
| Snippet (FR-013) | snippet around the first occurrence, with the terms marked |
| Isolation (SC-004) | B's `GET /api/search` contains nothing from A |
| Browser flow | Ctrl+Space, type, Enter opens the task from another week and selects the term; Esc gives focus back; offline, notice and local results; magnifier at 360 px with touch |

## Manual validation

1. Write "Café with Joana" in a task this week and "résumé" in the notes of a task in another project, two weeks ago. Ctrl+Space, "cafe joana": the task comes first; Enter opens it.
2. Search "resume": the result shows the snippet with the term highlighted; Enter goes to the old week, opens the snapshot and selects the word.
3. With the cursor in the notes, Ctrl+Space and Esc: the cursor goes back to the same spot.
4. In DevTools at 360 px with touch: the magnifier shows and the hint disappears; tap the magnifier and search.
5. Offline, search a term from a week already opened: it shows, with the local-content notice.
