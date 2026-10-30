# Implementation Plan: Images in notes

**Branch**: `008-images` | **Date**: 2026-10-29 | **Spec**: [spec.md](spec.md)

## Summary

- **Server**:
  - Table `image`, with the binary in SQLite itself (migration `006_image.sql`, later folded into `001_initial.sql`).
  - Module `images.py` with `PUT /api/images/{id}`, idempotent and with the ID generated on the client, and `GET /api/images/{id}`, own account only.
  - Sanitizing accepts `<img src="/api/images/<uuid>" width>`.
  - The backup carries the images in base64.
- **Client**:
  - Paste and drop shrink the image in a `canvas`, store it in IndexedDB (store `images`) and insert the reference.
  - Image upload runs along with the ops queue.
  - The service worker serves `/api/images/` network-first. Offline, it uses the stored copy; for an image not yet uploaded, it uses IndexedDB.
  - The image's right edge resizes.

## Constitution Check

| Principle | How it complies | Status |
| --- | --- | --- |
| I. Fewer controls | No new button: paste, drop and pull the edge | ✅ |
| III. Nothing is lost | An image pasted offline stays on the device and counts as pending until sent. Upload is idempotent | ✅ |
| IV. Isolated accounts | `GET`/`PUT` only with the session's `account_id`; another account's ID answers 404. The offline copy never replaces a server 404 | ✅ |
| Security | Type checked by the first bytes, not only by the header. `nosniff` is already on every response. `img` only with a `src` from the app itself | ✅ |
| V. Simplicity | Binary in SQLite (no file folder or storage service); shrinking with native `canvas` | ✅ |

## Decisions

- **R1. Binary in SQLite.** For images up to 5 MB, SQLite does fine. The database is a single file, and the server backup planned for deployment already includes the images. (`ponytail:` if the database grows past a few GB, move to files on disk.)
- **R2. Client ID.** The ID (UUID) generated in the browser lets the reference be inserted right away, even offline. A `PUT` with the same ID repeats with no effect.
- **R3. Service worker.** It tries the network first, and whatever succeeds goes into the `semana-images` cache. Only when the network fails does it use the cache or IndexedDB. A server 404 is never replaced by the cache, so another account is never shown an image stored in the same browser. On logout, the image cache is cleared.
- **R4. Pending changes.** `pending()` now adds up the account's ops and images, so the footer and the logout warning count the images.
- **R5. Server sanitizing.** `url_relative="pass_through"` with `attribute_filter`: on `img`, `src` must match `/api/images/<uuid>` and `width` a number between 16 and 4000; on `a`, `href` must be absolute (http, https, mailto, file), as before.

## Project Structure

```text
src/semana/migrations/006_image.sql  # now part of 001_initial.sql
src/semana/images.py                 # new
src/semana/app.py                    # includes the routes
src/semana/sanitize.py               # img
src/semana/backup.py                 # images in the backup
src/semana/static/sw.js              # /api/images/
src/semana/static/js/pure.js         # sanitizeHTML with img; shrinkImage
src/semana/static/js/data.js         # images store, upload, pending
src/semana/static/js/app.js          # paste, drop, edge
src/semana/static/app.css
tests/api/test_images_api.py, test_sanitize.py, test_backup_api.py, test_isolation.py
tests/e2e/test_images_in_notes.py
```
