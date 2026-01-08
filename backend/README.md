# Literature Explorer Backend

FastAPI-based microservice for querying and processing literary data from Wikidata.

## Overview

This backend provides a RESTful API that:
- Queries Wikidata's SPARQL endpoint for literary data
- Processes and transforms data into visualization-ready formats
- Caches responses using Redis for improved performance
- Calculates author similarity using Jaccard indices

## Quick Start

### With Docker (Recommended)
```bash
# From project root
docker-compose up --build backend redis
```

### Local Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Redis (required for caching)
docker run -d -p 6379:6379 redis:7-alpine

# Run the server
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Architecture

```
app/
├── main.py              # Application entry point, lifespan management
├── config.py            # Pydantic Settings configuration
│
├── routers/             # API endpoint definitions (FastAPI routers)
│   ├── search.py        # /api/search/* - Book/author search
│   ├── graph.py         # /api/graph/*  - Network visualization
│   ├── geo.py           # /api/geo/*    - Geographic data
│   └── recommendations.py  # /api/recommendations/*
│
├── services/            # Business logic layer
│   ├── wikidata_client.py    # SPARQL client with retry logic
│   ├── cache_service.py      # Redis Cache-Aside pattern
│   ├── search_service.py     # Book/author search logic
│   ├── graph_service.py      # Network graph construction
│   ├── geo_service.py        # Geographic processing
│   └── recommendation_service.py  # Similarity calculations
│
├── models/              # Pydantic data models
│   ├── book.py          # Book entity
│   ├── author.py        # Author entity
│   ├── graph.py         # GraphNode, GraphEdge, GraphData
│   ├── geo.py           # GeoPoint, GeoCluster, GeoResponse
│   └── location.py      # Location model
│
└── sparql/              # SPARQL query templates
    ├── template_loader.py   # Jinja2 template renderer
    └── templates/
        ├── search_books.sparql
        ├── author_graph.sparql
        ├── geo_locations.sparql
        └── get_author.sparql
```

## Services

### WikidataClient

Robust SPARQL client with:
- **Exponential backoff retry** for 429/503 errors
- **Timeout handling** (Wikidata has 60s limit)
- **Cache key generation** for consistent caching

```python
from app.services.wikidata_client import WikidataClient

client = WikidataClient()
results = await client.execute_query("""
    SELECT ?item ?itemLabel WHERE {
        ?item wdt:P31 wd:Q571.  # instance of book
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } LIMIT 10
""")
```

### CacheService

Redis caching with Cache-Aside pattern:

```python
from app.services.cache_service import CacheService

cache = CacheService()
await cache.connect()

# Get from cache
data = await cache.get("my_key")

# Set with TTL
await cache.set("my_key", {"data": "value"}, ttl_seconds=3600)
```

**TTL Strategy:**
| Data Type | TTL | Reason |
|-----------|-----|--------|
| Static (historical) | 7 days | Author/book data rarely changes |
| Search results | 24 hours | Balance freshness with performance |
| Warm cache | 30 days | Pre-cached popular queries |

### SearchService

Searches books with multi-filter support:

```python
from app.services.search_service import SearchService

service = SearchService(wikidata_client, cache_service)
books = await service.search_books(
    country_qid="Q30",      # USA
    genre_qid="Q1422746",   # Magic Realism
    year_start=1950,
    year_end=2000,
    limit=50
)
```

### GraphService

Builds author relationship networks:

```python
from app.services.graph_service import GraphService

service = GraphService(wikidata_client, cache_service)
graph = await service.get_author_network(
    author_qids=["Q23434", "Q188385"],  # Hemingway, Stein
    depth=2,
    include_movements=True
)
# Returns: GraphData with nodes, edges, centrality scores
```

### GeoService

Processes geographic data for map visualization:

```python
from app.services.geo_service import GeoService
from app.models.geo import GeoLayerType

service = GeoService(wikidata_client, cache_service)
locations = await service.get_locations(
    layer=GeoLayerType.BIRTHPLACES,
    author_qids=["Q23434"],
    cluster=True  # Enable server-side clustering
)
```

### RecommendationService

Finds similar authors using Jaccard similarity:

```python
from app.services.recommendation_service import RecommendationService

service = RecommendationService(wikidata_client, cache_service)
similar = await service.find_similar_authors(
    author_qid="Q23434",  # Hemingway
    limit=10
)
# Returns: [{"qid": "Q...", "name": "...", "similarity": 0.45, ...}]
```

## SPARQL Templates

Templates use Jinja2 syntax for dynamic query generation:

```sparql
{# templates/search_books.sparql #}
SELECT ?book ?bookLabel ?authorLabel WHERE {
    ?book wdt:P31 wd:Q571.  # instance of book
    ?book wdt:P50 ?author.  # has author
    
    {% if country_qid %}
    ?author wdt:P27 wd:{{ country_qid }}.  # nationality filter
    {% endif %}
    
    {% if year_start and year_end %}
    ?book wdt:P577 ?pubDate.
    FILTER(YEAR(?pubDate) >= {{ year_start }} && YEAR(?pubDate) <= {{ year_end }})
    {% endif %}
    
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT {{ limit }}
```

Usage:
```python
from app.sparql.template_loader import render_sparql

query = render_sparql(
    "search_books.sparql",
    country_qid="Q30",
    year_start=1920,
    year_end=1940,
    limit=100
)
```

## Wikidata Properties Reference

| Property | Name | Description |
|----------|------|-------------|
| P31 | instance of | Type classification (Q571=book) |
| P50 | author | Book's author |
| P27 | country of citizenship | Author's nationality |
| P19 | place of birth | Birthplace |
| P20 | place of death | Death place |
| P135 | movement | Literary movement |
| P136 | genre | Work's genre |
| P577 | publication date | When published |
| P625 | coordinate location | Geographic coordinates |
| P737 | influenced by | Intellectual influences |
| P840 | narrative location | Story setting |
| P1066 | student of | Mentor relationship |

## Configuration

Environment variables (or `.env` file):

```env
WIKIDATA_ENDPOINT=https://query.wikidata.org/sparql
REDIS_URL=redis://localhost:6379
CACHE_TTL_STATIC=604800
CACHE_TTL_SEARCH=86400
DEFAULT_QUERY_LIMIT=100
MAX_QUERY_LIMIT=500
QUERY_TIMEOUT=55
MAX_RETRIES=3
```

## Error Handling

The API returns appropriate HTTP status codes:

| Code | Meaning | Cause |
|------|---------|-------|
| 200 | Success | Request completed |
| 400 | Bad Request | Invalid QID format, missing params |
| 504 | Gateway Timeout | Wikidata query timeout |
| 503 | Service Unavailable | Wikidata temporarily down |
| 500 | Internal Error | Unexpected server error |

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html
```

## Dependencies

Key packages:
- `fastapi` - Web framework
- `pydantic` / `pydantic-settings` - Data validation
- `httpx` - Async HTTP client
- `redis` - Redis client (async)
- `tenacity` - Retry logic
- `networkx` - Graph algorithms
- `jinja2` - Template rendering
- `scikit-learn` - Jaccard similarity
