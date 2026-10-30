# Contributing to Semana

Thanks for your interest. A few agreements so your contribution lands in one piece:

## Before you code

- For behavior changes, open an issue first, describing the problem and not just the solution. Semana is small on purpose. The [project principles](.specify/memory/constitution.md) explain what usually stays out, such as extra controls and modal windows.
- New features follow the [Spec Kit](https://github.com/github/spec-kit) flow: specification, plan and tasks in `specs/NNN-name/`, and then the code.

## In the code

- Code, comments and docs are in English. The interface is in English by default, with a Brazilian Portuguese translation.
- UI strings live in `src/semana/static/js/i18n.js`, in two dictionaries (`en` and `pt-BR`). Every new string needs both. Don't hard-code text in the markup; use `t('some.key')`.
- The client is JavaScript with no build step (`src/semana/static/js`), and the server is FastAPI with SQLite and no ORM.
- Every database query filters by the session's account. Every new op needs a case in `tests/api/test_isolation.py`.
- Before sending, run `uv run ruff check src tests` and `uv run pytest`.

## License of contributions

Semana is distributed under the AGPL-3.0. By sending a contribution, you confirm that you have the right to send it and agree that:

1. it is licensed under the AGPL-3.0, like the rest of the project; and
2. the project maintainer may also distribute it under other terms, including in the version of Semana they host.

If you do not agree with item 2, say so in the pull request before it is accepted.
