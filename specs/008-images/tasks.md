---

description: "Tasks for feature 008: images in notes"
---

# Tasks: Images in notes

**Input**: [plan.md](plan.md), [spec.md](spec.md)

## Phase 1: Server

- [X] T001 Create `src/semana/migrations/006_image.sql`: table `image (id TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES account(id) ON DELETE CASCADE, mime TEXT NOT NULL CHECK (mime IN ('image/jpeg','image/png','image/gif','image/webp')), data BLOB NOT NULL, size INTEGER NOT NULL, created_at TEXT NOT NULL)` and an index on `account_id`. (Later folded into `001_initial.sql`.)
- [X] T002 Create `src/semana/images.py` and include it in `app.py`:
  - **`PUT /api/images/{id}`**:
    - The `id` must be a UUID, and the type comes from `Content-Type`, within the list. The first bytes must match the type; if they do not, 422.
    - Over 5 MB, 413 `{"error": "too_large"}`. If the account's total goes over 500 MB, 413 `{"error": "quota"}`.
    - If the ID already belongs to the account, 200. If it belongs to another account, 404. If it is new, store it and return 201.
  - **`GET /api/images/{id}`**: returns the bytes, with the type and `Cache-Control: private, max-age=31536000, immutable`. If the image is not the account's, 404.
- [X] T003 In `src/semana/sanitize.py`, accept `img` with `src` and `width` through the `attribute_filter` (R5); `a[href]` stays absolute only.
- [X] T004 In `src/semana/backup.py`:
  - **Export:** `images: [{id, mime, data}]`, with the data in base64.
  - **Import:** optional `images`. Each image gets a new ID, and the text of task notes, week notes and snapshots is rewritten with the new IDs. Images go in the same transaction, with the same limits.
- [X] T005 [P] Tests:
  - `tests/api/test_images_api.py`: round trip, idempotency, wrong type, bytes that do not match, too large, quota (with `monkeypatch` on the limit), deleting the account deletes the images.
  - `tests/api/test_sanitize.py`: keeps the app's image with a width; drops an external image, `onerror` and a `src` with `javascript:`.
  - `tests/api/test_backup_api.py`: the image goes and comes back, with the reference rewritten.
  - `tests/api/test_isolation.py`: `test_image_isolated`, where B can neither read nor overwrite A's image.

## Phase 2: Client

- [X] T006 In `src/semana/static/js/pure.js`:
  - `sanitizeHTML` accepts `IMG` with a `/api/images/<uuid>` `src` and a numeric `width`.
  - New `shrinkImage(file)`, which returns `{blob, mime}`, at most 1600 px; GIF passes with no shrinking, up to 5 MB.
- [X] T007 In `src/semana/static/js/data.js`:
  - IndexedDB version 2, with the `images` store.
  - `storeImage(id, mime, blob)`.
  - `sendImages()`, called at the start of `send()`.
  - `count` adds the pending images.
  - `clearAccount` deletes the account's images and the `semana-images` cache.
- [X] T008 In `src/semana/static/sw.js`, handle `GET /api/images/` per R3.
- [X] T009 In `src/semana/static/js/app.js`:
  - **Paste and drop:** pasting with image files calls `insertImages(files, range)`. Dropping does the same, at the drop point (`caretRangeFromPoint`). Outside the type list or over 20 MB, the warning shows. After inserting, `markNotesDirty()`.
  - **Edge:** `pointerdown` within 12 px of the image's right edge, in editable notes, resizes. At the end, it writes the `width` and calls `markNotesDirty()`. The cursor changes to `ew-resize` near the edge.
- [X] T010 In `src/semana/static/app.css`: `.notes img{max-width:100%;height:auto}`, with an outline on hover in editable notes.
- [X] T011 [P] In `tests/e2e/test_images_in_notes.py`, create `test_paste_and_shrink` (includes shrinking a 3000 px image), `test_drop_into_week_notes`, `test_edge`, `test_offline` and `test_invalid_type`.

## Phase 3: Polish

- [X] T012 `uv run ruff check src tests`, the full suite twice, and screenshots.
