# Architecture

```text
React + Recharts
      |
   REST API
      |
    FastAPI
      |
Security / Trust Engine
      |
    SQLite
```

Backend modules: `main.py` (API/state orchestration), `security.py` (cryptography and scoring), `db.py` (schema/persistence), `models.py` (validation), `seed.py` (fictional case-study data).

The authoritative state is stored in `devices.state` and changed only by backend workflows. Trust evaluations are append-only history records. Security events record significant failures and overrides.
