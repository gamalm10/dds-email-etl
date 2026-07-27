# DDS Email ETL - Agent Guidelines

## Tech Stack
- Python 3.12+ with FastAPI
- async SQLAlchemy 2.0 + aiomysql + MariaDB 11
- PI SDK (Node.js sidecar) via JSON-RPC over stdio
- pytest for testing
- Ruff for linting

## Code Quality
- Run lint after every code change
- Follow existing code conventions
- No comments unless requested
- pytest for testing

## Key Project Paths
- `api/main.py` - FastAPI app
- `core/models.py` - SQLAlchemy ORM models
- `core/schemas.py` - Pydantic schemas
- `services/` - Business logic (imap, parser, extraction, analytics, etc.)
- `migrations/001_init.sql` - Database schema
