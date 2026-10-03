# InsightForge AI

Phase 1 provides the FastAPI backend foundation for InsightForge AI. The API
currently exposes a health check at `GET /health`.

## Requirements

- Python 3.12
- `uv`

Install the project and its development dependencies from the project root:

```powershell
uv sync
```

## Run the API

```powershell
uv run uvicorn backend.app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive API docs are at
`http://127.0.0.1:8000/docs`.

## Run tests

```powershell
uv run pytest backend/tests
```

## Configuration

Application settings are read from the root `.env` file. Use `.env.example` as
a reference for the available settings: `APP_NAME`, `APP_ENV`, and `DEBUG`.
