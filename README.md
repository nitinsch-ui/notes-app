# Notes App

A small notes manager with categories, available as a REST API (FastAPI) and a terminal CLI. Both share the same SQLAlchemy models and SQLite database.

## Features

- Create, read, update (partial `PATCH`) and delete notes
- Organise notes into categories (one category per note)
- Search notes by title
- Data integrity: duplicate category names, notes pointing at missing categories, and deleting a category that still has notes are all rejected with clear HTTP errors (foreign keys are enforced in SQLite)

## Tech stack

Python 3.10+, FastAPI, SQLAlchemy 2.0, Pydantic v2, SQLite, pytest

## Getting started

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run the API

```bash
uvicorn main:app --reload
```

The API runs at http://127.0.0.1:8000. Interactive docs (Swagger UI) are at http://127.0.0.1:8000/docs.

### Run the CLI

```bash
python notes_app.py
```

Both use `notes.db` in the current directory. Set `DATABASE_URL` to use a different database, e.g. `DATABASE_URL=sqlite:///other.db`.

## API

| Method | Path | Description | Success | Errors |
|--------|------|-------------|---------|--------|
| POST | `/categories` | Create a category | 201 | 409 duplicate name |
| GET | `/categories` | List categories | 200 | |
| DELETE | `/categories/{id}` | Delete a category | 200 | 404 not found, 409 still has notes |
| POST | `/notes` | Create a note | 201 | 422 category doesn't exist |
| GET | `/notes?search=` | List notes newest-first, optionally filtered by title | 200 | |
| GET | `/notes/{id}` | Get one note | 200 | 404 |
| PATCH | `/notes/{id}` | Update only the fields sent | 200 | 404, 422 category doesn't exist |
| DELETE | `/notes/{id}` | Delete a note | 200 | 404 |

### Example

```bash
curl -X POST localhost:8000/categories -H "Content-Type: application/json" -d '{"name": "work"}'
curl -X POST localhost:8000/notes -H "Content-Type: application/json" \
     -d '{"title": "Standup", "content": "Discuss sprint goals", "category_id": 1}'
curl "localhost:8000/notes?search=Stand"
curl -X PATCH localhost:8000/notes/1 -H "Content-Type: application/json" -d '{"title": "Daily standup"}'
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests use FastAPI's `TestClient` against a temporary SQLite database, so your `notes.db` is never touched.

## Project structure

```
main.py          FastAPI app and endpoints
models.py        SQLAlchemy models, engine and session factory
schemas.py       Pydantic request/response schemas
notes_app.py     Terminal CLI
tests/           API tests (pytest + TestClient)
```
