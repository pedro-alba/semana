# Data Model: Appearance

## account (new column)

| Field | Type | Rules |
| --- | --- | --- |
| appearance | TEXT (JSON) | `NOT NULL DEFAULT '{}'`. Object with `theme`, `mode`, `font`, `palette` |

Accepted values (the prototype's, `specs/semana.html`, `THEMES`/`MODES`/`FONTS`/`PALETTES`):

| Key | Values | Default |
| --- | --- | --- |
| theme | `graphite`, `paper`, `ink` | `graphite` |
| mode | `light`, `dark`, `system` | `dark` |
| font | `theme`, `mono`, `sans`, `serif` | `theme` |
| palette | `classic`, `sunset`, `lavender`, `moss`, `traffic`, `neutral` | `classic` |

- The server only writes values from these lists, always all four together.
- The client treats a missing key or unknown value as that key's default.
- There is no revision: the last write wins ([R2](research.md)).

## Browser copy

`localStorage['semana-appearance']`: the same object. It is written on every change and when the account is received, stays on log out and is erased on account deletion.

## Attributes on `<html>` (the prototype's)

| Attribute | Source |
| --- | --- |
| `data-theme` | `theme` |
| `data-mode-pref` | `mode` |
| `data-mode` | `mode`, or `light`/`dark` from the system preference when `mode` is `system` |
| `data-font` | `font` |
| `data-palette` | `palette` |
