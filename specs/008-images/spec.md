# Feature Specification: Images in notes

**Feature Branch**: `008-images`

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "Paste or drag images into a task and change their size by dragging the edges." Owner's decisions (2026-10-29): images live on the server (the note keeps only the reference); the browser shrinks the image before sending (longer side up to 1600 px); pasting offline works and sends when the connection is back; it applies to task notes and to week notes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Paste or drag an image (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the cursor in a task's notes (or the week's), **When** the person pastes an image (screenshot, copied photo) or drags an image file into the text, **Then** the image appears at the cursor (or where it was dropped), without reloading, and is saved like the rest of the text.
2. **Given** a large photo (e.g. 4000 × 3000), **When** it is pasted, **Then** it is shrunk to at most 1600 px on the longer side before being stored.
3. **Given** a file that is not an image, or an image over 20 MB, **When** the person tries to paste or drag it, **Then** nothing is inserted and the app says "Use JPG, PNG, GIF or WebP images up to 20 MB."
4. **Given** the same account on another device, **When** the task is opened, **Then** the image shows.
5. **Given** a closed week, **When** the person opens it, **Then** the images show in the snapshot, read-only.

---

### User Story 2 - Change the size by the edge (Priority: P1)

**Acceptance Scenarios**:

1. **Given** an image in editable notes, **When** the pointer is over the right edge (or the bottom-right corner), **Then** the cursor shows it can be resized.
2. **Given** the edge pulled, **When** the person releases, **Then** the image takes the new width (aspect ratio kept), between 48 px and the text width, and the width is saved.

---

### User Story 3 - Offline and only for your own account (Priority: P2)

**Acceptance Scenarios**:

1. **Given** no connection, **When** the person pastes an image, **Then** it shows and is stored on the device; the footer shows pending changes until the image is sent when the connection is back.
2. **Given** another account, **When** it tries to open the address of an image that is not its own, **Then** it cannot (as if the image did not exist).
3. **Given** the backup (005), **When** the person exports and imports, **Then** the images go and come back along with it.

### Edge Cases

- Deleting the image from the text: it disappears from the note; the file stays on the server (cleanup of unused images is out of scope).
- HTML pasted from another site with an external `<img>`: the external image is dropped (only images uploaded to Semana are accepted).
- Per-account limit: 500 MB of images; above that the app says "The account's image limit has been reached."
- Animated GIF: stored as it came (no shrinking), if it is up to 5 MB.
- Logging out: this device's pending images follow the rule for other pending changes (warning on logout).
- Deleting the account: the images are deleted with it.

## Requirements *(mandatory)*

- **FR-001**: Pasting and dropping images MUST insert the image into the notes (task and week) at the cursor or drop point.
- **FR-002**: The browser MUST shrink images to at most 1600 px on the longer side (PNG stays PNG; others become JPEG), except GIF.
- **FR-003**: The image MUST live on the server, tied to the account, and the note MUST keep only the reference and, if any, the width.
- **FR-004**: Only the owning account MUST be able to read or write its images.
- **FR-005**: Pulling the right edge MUST change the width (48 px up to the text width), keeping the aspect ratio.
- **FR-006**: Offline, pasting MUST work; the image is sent when the connection is back and counts as a pending change.
- **FR-007**: Sanitizing (001 FR-035) MUST accept only Semana's own images, with an optional width, and drop any other.
- **FR-008**: The backup (005) MUST include the images.
- **FR-009**: Limits: 20 MB per source file; 5 MB per stored image; 500 MB per account.

## Success Criteria *(mandatory)*

- **SC-001**: Pasting a screenshot takes one gesture and shows in under 1 s.
- **SC-002**: A stored phone photo takes less than 600 KB.
- **SC-003**: Isolation tests record zero reads of another account's images.

## Assumptions

- Images live in the server database (SQLite), which puts them in the database backup planned for deployment.
- Cleanup of images that are no longer used is left for later.
- On a phone, resizing by the edge also works with a finger, starting at the edge.
