# Contributing to Literature Explorer

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- Git

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd Literature-Explorer

# Start all services with Docker
docker-compose up --build

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
```

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Redis (required)
docker run -d -p 6379:6379 redis:7-alpine

# Run server
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
├── backend/                 # FastAPI microservice
│   ├── app/
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── models/         # Pydantic models
│   │   └── sparql/         # SPARQL templates
│   └── requirements.txt
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── api/           # API client & hooks
│   │   └── types/         # TypeScript definitions
│   └── package.json
├── docs/                   # Documentation
└── docker-compose.yml
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Code Style

**Python (Backend):**
- Follow PEP 8
- Use type hints
- Add docstrings to functions and classes
- Run `black` for formatting
- Run `mypy` for type checking

```bash
cd backend
black app/
mypy app/
```

**TypeScript (Frontend):**
- Use TypeScript strict mode
- Follow ESLint rules
- Use functional components with hooks

```bash
cd frontend
npm run lint
npm run type-check
```

### 3. Testing

**Backend:**
```bash
cd backend
pytest
pytest --cov=app --cov-report=html
```

**Frontend:**
```bash
cd frontend
npm test
```

### 4. Commit Messages

Use conventional commits:

```
feat: add author timeline visualization
fix: resolve cache key collision
docs: update API reference
refactor: simplify graph service
```

### 5. Pull Request

1. Push your branch
2. Create a Pull Request
3. Fill out the PR template
4. Wait for review

## Areas for Contribution

### Good First Issues

- [ ] Add more country presets in FacetedSearchSidebar
- [ ] Improve loading states with skeleton screens
- [ ] Add unit tests for services
- [ ] Improve mobile responsiveness

### Feature Ideas

- [ ] Export visualizations as images
- [ ] Save and share searches
- [ ] Add more graph layout options
- [ ] Implement advanced search operators
- [ ] Add dark mode support

### Documentation

- [ ] Add more SPARQL query examples
- [ ] Create video tutorials
- [ ] Translate documentation

## Adding a New Feature

### Backend: New API Endpoint

1. **Create/update model** in `app/models/`
2. **Create service** in `app/services/`
3. **Create router** in `app/routers/`
4. **Register router** in `app/main.py`
5. **Add SPARQL template** in `app/sparql/templates/`
6. **Write tests**
7. **Update API documentation**

Example:
```python
# app/routers/new_feature.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/new-feature", tags=["New Feature"])

@router.get("/")
async def get_feature():
    """Endpoint description."""
    return {"status": "ok"}
```

### Frontend: New Component

1. **Create component** in `src/components/`
2. **Add types** in `src/types/index.ts`
3. **Create API hook** in `src/api/hooks.ts`
4. **Add to App.tsx** or parent component
5. **Add styles** to `src/styles/index.css`

Example:
```typescript
// src/components/NewComponent.tsx
import React from 'react';

interface NewComponentProps {
    data: SomeType;
}

export function NewComponent({ data }: NewComponentProps) {
    return <div>{/* ... */}</div>;
}
```

### Adding a New SPARQL Template

1. Create file in `backend/app/sparql/templates/`
2. Use Jinja2 syntax for dynamic parts
3. Test in Wikidata Query Service first
4. Add to template loader if needed

## Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Types are properly annotated
- [ ] Functions have docstrings
- [ ] No console.log or print statements
- [ ] Error cases are handled
- [ ] Tests are included
- [ ] Documentation is updated

## Getting Help

- Open an issue for bugs
- Start a discussion for feature requests
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
