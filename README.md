# DocsDrafter 2.0

DocsDrafter is a document drafting platform: upload templates, generate documents from them with AI assistance, and export to DOCX/PDF.

## Tech Stack

- **Backend:** FastAPI (Python), SQLAlchemy + Alembic, Celery workers
- **Frontend:** TypeScript web app

## Project Structure

```
backend/   FastAPI application, services, workers, tests
frontend/  Web client
```

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Copy `.env.example` to `.env` and fill in the required values.

### Run tests

```bash
cd backend
pytest
```

## License

All rights reserved.
