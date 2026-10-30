# Research: Calendar and due dates

The stack is the same as in feature 001 ([001 research](../001-accounts-weekly-core/research.md)), with no new dependency. This research records only the new decisions.

## R1. Occurrences computed on the client, with the prototype's code

- **Decision**: the server stores only the series (one row per event). The week's occurrences are computed on the client by the prototype's `occurrences` function, and overlaps by `layoutEvents`, both moved to `pure.js`.
- **Rationale**: both functions already implement FR-012 and FR-024: weekly and monthly recurrence, months without the day, inclusive end date and events that span days. With them on the client, the calendar works offline on cached data. The recurrence test (principle VI, SC-003) runs in the browser with `page.evaluate`, like the link tests in 001.
- **Alternatives**: expanding on the server would duplicate the rule in Python and need a connection to change weeks. An RRULE library is much larger than the spec's two frequencies.

## R2. Reading the agenda: one route per week

- **Decision**: `GET /api/agenda?week=` returns two lists, across all projects:
  - **Events**: the series that may have an occurrence in the week, from a rough SQL filter that leaves the exact cut to `occurrences`.
  - **Due dates**: the week's due dates. In the current week, it also includes overdue due dates of open tasks.
- The client caches this response under the key `agenda|<monday>` (FR-041).
- **Rationale**: the task list is loaded per project (`/api/week`), but the agenda and the due-dates band cover all projects and do not depend on the task's week (FR-030, FR-032). One route serves both the calendar and the overview.
- **Alternatives**: loading every task in the account to find due dates does not scale and does not fit in the cache. Adding the agenda to `/api/week` would repeat it on every project switch.

## R3. Event conflicts: one revision per row

- **Decision**: `event.rev`. The `event.save` operation carries every field and `base_rev`:
  - **Create**: the row does not exist and `base_rev` is 0.
  - **Write**: `base_rev` equals the current revision. Writes and increments.
  - **Resend**: every field equals the current ones. Responds `ok`.
  - **Conflict**: in all other cases, responds with the current event in `value`.
  - **Deleted on another device**: the row does not exist and `base_rev` is greater than 0. It is a conflict with `value: null`. If the person keeps their version, the resend with `base_rev` 0 recreates the event.
- **Delete**: `event.delete` is unconditional and idempotent. The person has already confirmed in the editor (FR-025).
- **Rationale**: the spec treats the event as one unit (FR-042), and the editor saves the whole form at once, as in the prototype.
- **Alternatives**: one revision per field, as on tasks, makes no sense for a form saved all at once.

## R4. Due date: a task column, last write wins

- **Decision**: column `task.due` (date or NULL) and the `task.due` operation, which touches `updated_at` (FR-005).
  - **On rollover**: the task is moved with all its columns, so the due date goes along.
  - **In the snapshot**: the due date gets in through `task_json` (FR-007).
- **Rationale**: the field has no text to merge. The spec decides that the last write wins.

## R5. Local times

- **Decision**: `start`, `end` and `until` are stored as local civil text (`YYYY-MM-DDTHH:MM` and `YYYY-MM-DD`), as in the prototype. All-day events store an exclusive `end` (midnight of the day after the last one). There is no conversion to UTC.
- **Rationale**: the time zone belongs to the account and does not change in this feature (FR-043). A meeting "every Tuesday at 9:00" stays at 9:00 after daylight saving time.
- **Alternatives**: UTC with conversion would shift recurring events when the time zone changed offset.

## R6. Server-side validation

- **Decision**: `event.save` validates in the pydantic model:
  - title from 1 to 160 characters;
  - `end > start` and at most 31 days long;
  - `repeat` one of `none`, `weekly` and `monthly`;
  - `until` required if there is recurrence, absent if there is not, and `until >= date(start)`;
  - location up to 500 characters and description up to 10,000, as plain text;
  - `project_id`, if given, from the same account. If not, `not_found`.

  The editor runs the same checks before queueing, with messages in the UI language (FR-022).
- **Rationale**: validation at the trust boundary applies to all stored data (constitution IV). Plain text needs no HTML sanitizing, because it is always shown through `esc`.
