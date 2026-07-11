# CyboPal Backend

FastAPI backend for the factory calibration workflow.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Use mock SSH for UI development without a device:

```bash
set CYBOPAL_SSH_MOCK=true
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Test

```bash
python -m unittest discover -s tests
```

