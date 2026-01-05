# Literature Explorer - Backend

FastAPI-based backend for the Literature Explorer data exploration platform.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run Development Server

```bash
uvicorn app.main:app --reload
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

Create a `.env` file:

```
REDIS_URL=redis://localhost:6379
WIKIDATA_ENDPOINT=https://query.wikidata.org/sparql
```
