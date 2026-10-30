# Quickstart: Appearance

Running and prerequisites are the same as in [feature 001](../001-accounts-weekly-core/quickstart.md).

## Automated tests

```sh
SEMANA_CHROMIUM=/usr/bin/chromium uv run pytest
```

| Rule | The test proves |
| --- | --- |
| Operation (contract) | `account.appearance` writes the four choices; a value outside the list is `invalid`; `/api/start` and `/api/login` return `appearance` |
| Isolation (FR-015) | B's operation does not change A's appearance |
| Instant switch (FR-002, SC-005) | with a task open and the cursor in the notes, changing each choice changes `<html>`, keeps the task open, the text and the cursor |
| Other device (SC-003) | choices made in one browser context show when signing in from a second context |
| First paint (SC-004) | on reload, online and offline, `<html>` already has the chosen appearance when `<body>` appears |
| Offline pending change (FR-012) | a choice made offline survives an offline reload and reaches the server when the connection returns |
| Contrast (SC-002) | in each theme and mode, card text has contrast ≥ 4.5:1 against the background at the 0%, 50% and 100% stops of the six gradients |

## Manual validation

1. Open a task and put the cursor in the middle of the notes. In the profile menu, change theme, mode, font and gradient: everything changes right away, the task stays open and the cursor stays in place.
2. Pick System mode and switch the operating system's theme: the app follows.
3. Pick Ink, Light, Serif and Moss. Open another private window and sign in to the same account: the appearance is the same.
4. Reload the page: dark Graphite does not show even for an instant.
5. At 360 px in DevTools, open the profile menu: everything is reachable by scrolling inside the menu, with no sideways scrolling.
6. Log out: the sign-in screen keeps the appearance. Sign in with another account: its appearance applies.
