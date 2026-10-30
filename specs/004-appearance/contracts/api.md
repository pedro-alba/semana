# API contract: Appearance

Conventions from the [001 contract](../../001-accounts-weekly-core/contracts/api.md).

## `appearance` field on the `account` object

The `account` object returned by `POST /api/account`, `POST /api/login` and `GET /api/start` gains:

```json
{"id": "…", "email": "…", "timezone": "America/Sao_Paulo",
 "appearance": {"theme": "paper", "mode": "system", "font": "serif", "palette": "moss"}}
```

An account that never chose returns `"appearance": {}`, and the client applies the defaults ([data-model](../data-model.md)).

## `account.appearance` operation

Goes through `POST /api/ops`, like the others.

```json
{"op": "account.appearance", "theme": "paper", "mode": "system", "font": "serif", "palette": "moss"}
```

- All four keys are required, with the values from the [data-model](../data-model.md). A value outside the list returns `{"status": "invalid", "fields": [...]}`.
- Writes to the session's account and returns `{"status": "ok"}`. Repeating the operation writes the same value.
- No revision and no conflict: the last one received wins.
