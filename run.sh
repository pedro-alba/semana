#!/bin/sh
# Runs Semana locally at http://localhost:8000 (Ctrl+C to stop).
# There is no default login: create an account on the screen itself. The password recovery link shows up here in the terminal.
cd "$(dirname "$0")"
SEMANA_DB=./dev.sqlite3 SEMANA_SECURE_COOKIE=0 exec uv run uvicorn semana.app:app --reload
