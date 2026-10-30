# Semana

Notes and tasks, one week at a time.

Semana replaces the text document full of highlights with tasks that have their own notes, organized by week. The current week is the focus. Whatever is not done moves to the next week by itself, and closed weeks are kept as read-only snapshots.

## Features

- **Tasks for the week:**
  - Tasks per project, with progress shown as color.
  - Subtasks, due dates and an "important" flag.
  - Notes with simple formatting, links and images.
- **Week notes**, for what is not a task.
- **Calendar:** one-off or recurring events (daily, weekly, monthly) that you drag with the mouse and resize by the edge. A single occurrence can be changed or deleted without touching the rest of the series.
- **Search** across tasks, notes and events (Ctrl+Space or the magnifier).
- **Works offline:** changes stay on the device and are sent when the connection is back. Conflicts between devices are never resolved silently.
- **Appearance saved in the account:** Graphite, Paper and Ink themes, light or dark mode, font and progress gradient.
- **Two languages:** the interface is in English by default, with a Brazilian Portuguese translation. It follows the browser language, or the choice in the profile menu (Language: Automatic, English, Português (Brasil)).
- **Backup:** export and import the whole account as JSON, including from the single-file prototype (`specs/semana.html`).
- **Isolated accounts:** each person only sees and changes their own data.

## Run locally

Requirement: [uv](https://docs.astral.sh/uv/). It installs Python 3.12 by itself.

```sh
uv sync
./run.sh              # http://localhost:8000
```

Create an account on the start screen. With no e-mail configured, the password reset link is printed in the terminal.

## Configuration

All configuration is done with environment variables. The [`.env.example`](.env.example) file lists and explains each one. Copy it to `.env.local`, which Git ignores, and run:

```sh
uv run --env-file .env.local uvicorn semana.app:app
```

## Self-hosting

Semana is a single Python process with one SQLite file. To put it online:

- **HTTPS:** a reverse proxy, such as Caddy or nginx. Set `SEMANA_BASE_URL` to the public address (it is used in password reset links). In production, leave `SEMANA_SECURE_COOKIE` unset, so the session cookie is `Secure` (`0` turns that off for local HTTP only).
- **Database:** point `SEMANA_DB` to a persistent path. Back up that file; it includes the images. `sqlite3 semana.sqlite3 ".backup copy.sqlite3"` copies it safely even while the server is running.
- **E-mail:** an SMTP provider, in `SEMANA_SMTP_HOST`, `SEMANA_SMTP_PORT`, `SEMANA_SMTP_USER`, `SEMANA_SMTP_PASSWORD` and `SEMANA_SMTP_FROM`. The password reset e-mail goes out in the account's language.
- **Legal pages:** `/terms` and `/privacy` are served per language: `terms.html` and `privacy.html` in English, `terms.pt-BR.html` and `privacy.pt-BR.html` in Portuguese (picked from the browser language, or with `?lang=pt-BR`). The ones in the repository are templates with `[PLACEHOLDERS]`. Put your filled-in versions, with the same file names, in a folder and point `SEMANA_CUSTOM_DIR` to it; any file missing there falls back to the template. These texts depend on who runs the service; review them with whoever handles the legal side.
- **Source code:** if you host a modified version, the AGPL-3.0 asks you to offer the source code to your users. Set `SEMANA_SOURCE_URL` to your repository's address; the link shows in the profile menu.

## Tests

```sh
uv run playwright install chromium   # once
uv run pytest                        # API and browser
uv run ruff check src tests
```

If Playwright's Chromium does not download, the system one works too: `SEMANA_CHROMIUM=/usr/bin/chromium uv run pytest`.

## How the project was built

Each feature went through a specification, a plan and tasks with [Spec Kit](https://github.com/github/spec-kit). The documents live in [`specs/`](specs/), one folder per feature (for example [`specs/001-accounts-weekly-core`](specs/001-accounts-weekly-core/) and [`specs/008-images`](specs/008-images/)), and the project principles in [`.specify/memory/constitution.md`](.specify/memory/constitution.md). The original prototype, a single HTML file that works without a server, is [`specs/semana.html`](specs/semana.html); its interface was translated to English.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[GNU Affero General Public License v3.0](LICENSE) or later.

The Roboto Mono font, embedded in the CSS, is distributed under the SIL Open Font License 1.1.
