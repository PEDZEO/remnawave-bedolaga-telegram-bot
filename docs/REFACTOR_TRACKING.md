# Refactor Tracking: remnawave-bedolaga-telegram-bot

## Rules
- We explicitly follow `/home/pedzeo/AGENTS.md` for all refactor steps.
- Changes are atomic, scoped, and reversible.
- Validation after each step whenever tooling is available.

## Progress Log

### 2026-02-21
- [x] Started backend phase 5 bootstrap decomposition.
- [x] Extracted runtime logging setup from `main.py` into `app/bootstrap/runtime_logging.py`.
- [x] Kept startup order and behavior unchanged (same formatter inputs, same log-rotation branch logic).
- [x] Extracted graceful signal handling from `main.py` into `app/bootstrap/signals.py`.
- [x] Kept shutdown flow behavior unchanged (`SIGINT`/`SIGTERM` still set `killer.exit=True`).
- [x] Extracted database migration startup stage from `main.py` into `app/bootstrap/database_startup.py`.
- [x] Kept migration behavior unchanged (`SKIP_MIGRATION` and `ALLOW_MIGRATION_FAILURE` semantics preserved).
- [ ] Continue backend phase 5 with next atomic extraction from `main.py`.

## Validation
- Attempted `make lint` -> failed: `uv: No such file or directory`.
- Attempted `make test` -> failed: `uv: No such file or directory`.
- Fallback `python -m pytest -q` -> failed: `No module named pytest`.
- `python -m py_compile main.py app/bootstrap/runtime_logging.py app/bootstrap/signals.py` -> success.
- `python -m py_compile main.py app/bootstrap/runtime_logging.py app/bootstrap/signals.py app/bootstrap/database_startup.py` -> success.
- Result: local environment currently lacks required Python tooling; code validation is limited to static review in this step.
