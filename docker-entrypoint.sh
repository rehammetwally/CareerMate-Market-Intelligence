#!/bin/sh
# =============================================================
# CareerMate Edge Evaluation Container — Entrypoint
# =============================================================
set -e

case "" in
  --benchmark)
    echo "[CareerMate] Running GlobalOccupational-Eval-2026 benchmark (mode: )..."
    cd /app/backend
    python -m pytest tests/ -v --tb=short
    ;;
  --test)
    echo "[CareerMate] Running integration test suite..."
    cd /app/backend
    python -m pytest tests/ -v --tb=short
    ;;
  --health)
    echo "[CareerMate] KG health check..."
    python -c "import sys; sys.path.insert(0,'/app/backend'); from market import get_market_kg; kg=get_market_kg(); print('OK: ' + str(len(kg.get('roles',{}))) + ' nodes loaded')"
    ;;
  *)
    echo "[CareerMate] Starting FastAPI edge server on port ..."
    exec python -m uvicorn app:app \
      --app-dir /app/backend \
      --host 0.0.0.0 \
      --port  \
      --workers 1 \
      --log-level info
    ;;
esac
