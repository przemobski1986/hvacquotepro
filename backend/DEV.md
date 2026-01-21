# HVACQuotePro backend – DEV

## Smoke tests (isolated)

Uruchamia pelny pipeline w izolacji od app.db:
- check na zakazane func.now()
- migracje Alembic do app_smoke.db
- seed admina i danych referencyjnych
- start API na porcie 8001
- uruchomienie smoke testow
- zatrzymanie API

### Run
powershell -ExecutionPolicy Bypass -File .\run_smoke_isolated.ps1

### Artifacts
- Baza smoke: app_smoke.db
- Port smoke API: 8001
- Skrypty:
  - run_smoke_isolated.ps1
  - check_no_func_now.py
  - scripts_seed_admin.py
  - scripts_seed_smoke_data.py
  - run_smoke.py
  - smoke_timekeeping.py
  - smoke_timekeeping_stop.py

## Notes
- Smoke testy nie dotykaja app.db.
- Przy modelach czasu nie uzywaj func.now() / server_default=func.now() – preferuj pythonowy default/onupdate.
