# storage-scraper — Code Style & Conventions

## General
- Python 3.11+; use `from __future__ import annotations` for forward refs
- Type hints on all function signatures
- Module-level docstrings on every file explaining its purpose
- Class-level docstrings on models and service classes

## Naming
- Snake_case for functions, variables, module names
- PascalCase for classes
- SCREAMING_SNAKE for constants (BASE_URL, IMAGE_DIR)
- Pydantic models for request bodies: `<Resource>Create`, `<Resource>Update`

## FastAPI patterns
- All routers in `app/api/<module>.py`, included in `app/main.py`
- Use `Depends(get_db)` for DB sessions
- Private helper `_<resource>_dict()` in each router file to serialize ORM models
- Pydantic v2 (`model_dump(exclude_none=True)`)

## SQLAlchemy patterns
- All models in `app/models.py` with `DeclarativeBase`
- Relationships defined with `back_populates`
- Cascade `"all, delete-orphan"` on child collections
- `onupdate=datetime.utcnow` on `updated_at` columns

## AI/ML conventions
- `generate_recommendation(listing, db)` returns a plain dict (not ORM model)
- Score range: 0.0–1.0; clamped with `max(0, min(1, score))`
- Model version tracked as `MODEL_VERSION` constant string in recommender.py
- Reasoning is a pipe-delimited string of human-readable factors

## Line length: 100 chars (ruff config)
