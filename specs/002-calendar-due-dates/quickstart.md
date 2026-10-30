# Quickstart: Calendar and due dates

The prerequisites and the run command are the same as in [feature 001](../001-accounts-weekly-core/quickstart.md). The `002_calendar.sql` migration (the `task.due` column and the `event` table, now part of `migrations/001_initial.sql`) runs by itself on startup.

## Automated tests

```sh
uv run pytest                                          # everything, including 001
SEMANA_CHROMIUM=/usr/bin/chromium uv run pytest tests/e2e   # browser with the system Chromium
```

| Rule | The test proves |
| --- | --- |
| Recurrence (SC-003) | `occurrences` over 24 months: weekly, monthly on the 31st, 30th and 29th (February and leap year), inclusive end date, turn of the year, event that crosses midnight and multi-day all-day event |
| Overlap | `layoutEvents` lays out simultaneous events in columns |
| Event conflict (FR-042) | a concurrent edit gives `conflict` with the current event; an edit on a deleted event gives `conflict` with `null`; an identical resend gives `ok` |
| Validation (FR-022, FR-023) | end before start, more than 31 days, `until` without recurrence, recurrence without `until`, and `until` before the start: all `invalid` |
| Due dates in the agenda (FR-030, FR-032) | due dates from all projects, overdue ones only in the current week |
| Rollover and snapshot (FR-002, FR-007) | the due date is kept on carry-over and shows in the snapshot |
| Isolation (SC-005) | new cases in `tests/api/test_isolation.py` and `GET /api/agenda` |
| Offline (SC-006) | an event created and a due date changed with no network reach another browser context |

## Manual validation

1. **Due dates**: open a task, use "Due date" and check the card texts for today, tomorrow, another day this week, a future date and a past one. Finish the task and see the due date leave the card. Move the clock to the next week (`SEMANA_NOW`, see 001) and check that the due date is still on the carried-over task.
2. **Calendar**: in "Calendar", create an event by clicking at 14:00 and another through the button. Create a weekly event until 3 weeks from now and confirm the 4th week has no occurrence. Create a monthly event on the 31st and confirm February has no occurrence. Put two events at the same time and see the columns. Try the project filter. Delete a series and see the confirmation in the editor.
3. **Agenda**: with due dates in two projects and one due date that passed last week, check "On the agenda" in the current week's overview: overdue ones come first and due dates show before events of the same day. Activate a due date and an event.
4. **Connection and conflict**: with no network, create an event and change a due date. Close and reopen the tab, reconnect and check in another window. Edit the same event in two windows and save in both: the second one sees the warning.
5. **Keyboard and mobile**: at 360 px, create an event and set a due date using only the keyboard.
