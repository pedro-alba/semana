# Research: Appearance

## R1. Apply before the first paint

**Decision**: a classic script, `/js/appearance.js`, loaded with `<script src>` in the `<head>` of `index.html`, `terms.html` and `privacy.html`, before the CSS. It reads `localStorage['semana-appearance']` and sets `data-theme`, `data-mode-pref`, `data-mode`, `data-font` and `data-palette` on `<html>`. The same file exposes `window.appearance` (`apply(p)`, `current()`, `VALUES`), which `app.js` uses; the value logic and System mode live in one place.

**Rationale**: the app's CSP (`default-src 'self'`, no `'unsafe-inline'` for scripts) forbids the inline script the prototype used. `app.js` is a module, deferred, and runs after the first paint, so it would show dark Graphite for an instant. A synchronous classic script in the `<head>` blocks painting until the attributes are set.

**Alternatives considered**: relaxing the CSP with a script hash (one more thing to keep in sync); having the server write the attributes into the HTML (needs to read the session to serve static files and does not help offline); a cookie with the appearance (the service worker returns the HTML from the cache, so the cookie never arrives).

## R2. One JSON column, last write wins

**Decision**: `account.appearance TEXT NOT NULL DEFAULT '{}'`, with the four keys. The `account.appearance` operation always writes all four, with no revision. The client fills missing or unknown keys with the default.

**Rationale**: the spec asks for "the last one received wins" and no conflict warning (appearance is not content). The operation is idempotent by nature (repeating writes the same thing). A JSON column accepts a new theme without a migration; in SQLite, changing a `CHECK` means rebuilding the table.

**Alternatives considered**: four columns with `CHECK` (another migration for every new value); a key-value `preference` table (one row per account does not justify a table); per-field revision like tasks (a conflict the spec says it does not want).

## R3. Offline and pending changes versus the cache

**Decision**:
- The change applies right away (attributes and `localStorage`) and enters the queue like other operations, coalesced by the same mechanism as text operations (`TEXT` in `data.js`), so only the last choice stays pending.
- In `data.start()`, if there is a pending `account.appearance` in the queue, the operation's appearance replaces the one in the response (server or cache), as is already done with projects created offline.
- On receiving the account (`start`), the client applies `account.appearance` and writes the browser copy.

**Rationale**: without the overlay, reloading offline would bring the old appearance from the `/api/start` cache over the new choice.

## R4. Other device and account switch

**Decision**:
- On returning to the tab (`visibilitychange`), `onReturn()` now requests `data.start()` and applies whatever appearance comes back, besides what it already reloads.
- On signing in with another account, `start` applies the new account's appearance.
- On log out, the browser copy stays (the sign-in screens use the last appearance).
- On account deletion, the `semana-appearance` key is erased and the page goes back to the default.

**Rationale**: it is the same moment content from another device shows up (feature 001). Nothing else in the app updates live.
