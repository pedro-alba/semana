# Research: Prototype import and backup

## R1. Where to convert and validate

**Decision**:
- **Conversion:** a prototype file is converted in the browser. The code of `migrate`, `normalize`, `validateState` and `assignOrder` is copied with no logic change into `pure.js`, and a new function, `fromPrototype`, translates the v2 state into the app's format.
- **Validation:** the server validates any file again, in full, and only the server writes.
- **Export:** built on the server.

**Rationale**: the v1 conversion already exists and was tested in the prototype, in JS. Rewriting it in Python would duplicate subtle rules (reports, actions, links). The server's validation is the one that counts, because the client is not trusted. The client's validation only avoids asking for confirmation on a file that will fail.

**Alternatives considered**: convert the prototype on the server (rewrite `migrate` in Python); export on the client from the cache (it could come out incomplete, since the cache only has the open weeks).

## R2. New IDs on every import

**Decision**: the server generates a new UUID for each project, task, subtask, log entry and event, and keeps a map from old ID to new ID to rebuild the links. In snapshots, `project_id` and the task `id` go through the same map; a snapshot task with no ID in the map gets a new one.

**Rationale**:
- IDs are a global primary key. Importing one account's backup into another, or the same file into two accounts, would collide.
- Always generating, instead of only on collision, is simpler and does not reveal whether an ID exists in another account.
- The cost is changing the IDs in the account itself. That does not matter, because everything is replaced and the device cache is cleared.
- Prototype IDs such as `pessoal` also become UUIDs.

## R3. Replace in one transaction

**Decision**:
- In a single transaction (`transaction(con)`, which is `BEGIN IMMEDIATE`): `DELETE FROM project WHERE account_id = ?`, which cascades to tasks, subtasks, log, notes and events with a project. Then `DELETE` from the account's `event` and `snapshot`, and the `INSERT`s.
- `processed_week` gets the file's value, capped at `monday(current) - 7`.
- After the `COMMIT`, `rollover.apply`.
- Revisions start over: 0 on text fields, 1 on events.

**Rationale**: the foreign keys with `ON DELETE CASCADE` exist since 001. Any exception in the middle undoes everything (FR-023, SC-003). The rollover after the `COMMIT` is the same one that runs in `/api/start`.

## R4. Pending changes and other devices

**Decision**:
- **Export:** first, the client calls `data.send()` and checks `pending() === 0`. With no connection, or with pending changes that did not go out, it shows the warning.
- **Import:** the confirmation shows `pending()`. After the import, `data.clearAccount(id)` clears the account's queue and cache, and `enter()` reloads everything.
- **Other device:** pending ops on IDs that no longer exist get `not_found`, which the queue already treats as a discard (001).

**Rationale**: reuses what exists. No new conflict rule.
