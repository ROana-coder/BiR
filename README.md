# Literature Explorer

**A Big Data Retriever & Visualization Platform for Literary Network Exploration**

> Built for the "Big Data Retriever" assignment: A microservice-based platform to intelligently query, visualize, and recommend literary resources using Wikidata.

Literature Explorer is a sophisticated web application that enables users to explore global literary networks, visualize author migrations, and discover connections between literary movements across time and space.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [Use Cases](#️-use-cases-implemented)
- [Technology Stack](#️-technology-stack)
- [Architecture Overview](#-architecture-overview)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Backend Services](#-backend-services)
- [Frontend Components](#-frontend-components)
- [Data Models](#-data-models)
- [Configuration](#️-configuration)
- [Development Guide](#-development-guide)

### 📚 Additional Documentation

- [Backend README](./backend/README.md) - Backend service details and usage
- [Frontend README](./frontend/README.md) - Frontend components and setup
- [API Reference](./docs/API_REFERENCE.md) - Complete API endpoint documentation
- [Wikidata Guide](./docs/WIKIDATA_GUIDE.md) - SPARQL queries and Wikidata integration

---

## 🚀 Key Features

*   **Intelligent Knowledge Retrieval**: Dynamically queries [Wikidata](https://www.wikidata.org/) using optimized SPARQL templates to fetch high-fidelity data about authors, books, and literary movements.
*   **Interactive Visualizations**:
    *   **🗺️ Map View**: Dual-layer geospatial visualization showing **Author Birthplaces** (Red Pins) and **Narrative Locations** (Blue Pins) to contrast where authors lived vs. where their stories are set.
    *   **🔗 Network Graph**: Force-directed graph revealing influence networks and shared stylistic movements.
    *   **📅 Timeline**: Interactive timeline of literary publications to identify historical trends.
*   **Faceted Search**: Filter large datasets by Nationality, Genre, and Time Period.
*   **Smart Recommendations**: Suggests similar authors based on shared movements, genres, and eras using Jaccard similarity indices.
*   **Resilient Architecture**:
    *   **Caching**: Redis-based "Cache-Aside" strategy to handle Wikidata API limits and improve latency.
    *   **Microservices**: Modular FastAPI backend and React frontend.
    *   **Robustness**: Exponential backoff retry logic for 3rd party API stability.

---

## 🏛️ Use Cases Implemented

### 1. The "Lost Generation" & Transatlantic Modernism
**Goal**: Visualize the influence of American expatriate writers in Europe.
*   **Visual Proof**: The Map View highlights a cluster of **Birthplaces** in the USA (Midwest/East Coast) while the **Narrative Locations** and biography centers shift to Paris, London, and Spain.

### 2. Magic Realism: A Global Phenomenon
**Goal**: Trace the spread of a specific genre beyond its Latin American roots.
*   **Visual Proof**: Selecting the "Magic Realism" preset reveals a dense network of Latin American authors (García Márquez, Allende) connected to global authors (Murakami, Rushdie), visualizing cross-cultural literary influence.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python 3.11, FastAPI, Pydantic, SPARQLWrapper, NetworkX, scikit-learn, tenacity |
| **Frontend** | React 18, TypeScript, Vite, D3.js, React-Leaflet, TanStack Query |
| **Data Source** | Wikidata SPARQL Endpoint |
| **Infrastructure** | Docker, Docker Compose, Redis 7 |

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐    │
│  │ MapView  │ │ForceGraph│ │ Timeline │ │FacetedSearchSidebar│   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘    │
│       │            │            │                │               │
│       └────────────┴────────────┴────────────────┘               │
│                            │                                     │
│                   TanStack Query + Axios                         │
└────────────────────────────┼────────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────┼────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     API Routers                           │   │
│  │  /api/search  │  /api/graph  │  /api/geo  │  /api/recommend │ │
│  └───────┬───────────────┬────────────┬────────────┬────────┘   │
│          │               │            │            │             │
│  ┌───────▼───────────────▼────────────▼────────────▼────────┐   │
│  │                    Services Layer                         │   │
│  │ SearchService │ GraphService │ GeoService │ RecommendSvc │   │
│  └───────┬───────────────┬────────────┬────────────┬────────┘   │
│          │               │            │            │             │
│  ┌───────▼───────────────▼────────────▼────────────▼────────┐   │
│  │              WikidataClient + CacheService                │   │
│  └───────┬───────────────────────────────────────┬──────────┘   │
└──────────┼───────────────────────────────────────┼──────────────┘
           │                                       │
           ▼                                       ▼
    ┌──────────────┐                      ┌──────────────┐
    │   Wikidata   │                      │    Redis     │
    │ SPARQL API   │                      │    Cache     │
    └──────────────┘                      └──────────────┘
```

---

## 📦 Getting Started

### Prerequisites
*   Docker & Docker Compose

### Installation & Run

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd Literature-Explorer
    ```

2.  **Launch with Docker Compose** (Recommended)
    This builds the frontend, backend, and Redis cache containers.
    ```bash
    docker-compose up --build
    ```

3.  **Access the Application**
    *   **Frontend**: [http://localhost:3001](http://localhost:3001)
    *   **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
    *   **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📂 Project Structure

```
├── docker-compose.yml       # Container orchestration
├── README.md                # This documentation
│
├── backend/                 # FastAPI Microservice
│   ├── Dockerfile
│   ├── requirements.txt     # Python dependencies
│   └── app/
│       ├── main.py          # Application entry point & lifespan
│       ├── config.py        # Environment configuration (Pydantic Settings)
│       │
│       ├── routers/         # API endpoint definitions
│       │   ├── search.py    # /api/search/* - Book search endpoints
│       │   ├── graph.py     # /api/graph/*  - Network graph endpoints
│       │   ├── geo.py       # /api/geo/*    - Geographic data endpoints
│       │   └── recommendations.py  # /api/recommendations/*
│       │
│       ├── services/        # Business logic layer
│       │   ├── wikidata_client.py    # SPARQL client with retry logic
│       │   ├── cache_service.py      # Redis Cache-Aside implementation
│       │   ├── search_service.py     # Book/author search logic
│       │   ├── graph_service.py      # Network graph construction
│       │   ├── geo_service.py        # Geographic data processing
│       │   └── recommendation_service.py  # Jaccard similarity engine
│       │
│       ├── models/          # Pydantic data models
│       │   ├── book.py      # Book entity model
│       │   ├── author.py    # Author entity model
│       │   ├── graph.py     # GraphNode, GraphEdge, GraphData
│       │   ├── geo.py       # GeoPoint, GeoCluster, GeoResponse
│       │   └── location.py  # Location model
│       │
│       └── sparql/          # SPARQL query templates
│           ├── template_loader.py   # Jinja2 template renderer
│           └── templates/
│               ├── search_books.sparql
│               ├── author_graph.sparql
│               ├── geo_locations.sparql
│               └── get_author.sparql
│
└── frontend/                # React Application
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts       # Vite configuration with proxy
    ├── tsconfig.json
    └── src/
        ├── main.tsx         # React entry point
        ├── App.tsx          # Main application component
        │
        ├── api/             # API client layer
        │   ├── client.ts    # Axios client with interceptors
        │   └── hooks.ts     # TanStack Query hooks
        │
        ├── components/      # React components
        │   ├── ForceGraph.tsx           # D3.js force-directed graph
        │   ├── BooksForceGraph.tsx      # Author-book relationship graph
        │   ├── MapView.tsx              # React-Leaflet map
        │   ├── Timeline.tsx             # Publication timeline
        │   ├── FacetedSearchSidebar.tsx # Search filters
        │   ├── AuthorDetailModal.tsx    # Author detail view
        │   ├── AuthorWorksList.tsx      # Author works list
        │   └── EmptyState.tsx           # Loading/error states
        │
        ├── types/           # TypeScript definitions
        │   └── index.ts     # Shared interfaces
        │
        └── styles/
            └── index.css    # Global styles
```

---

## 📖 API Documentation

### Base URL
- **Development**: `http://localhost:8000/api`
- **Swagger UI**: `http://localhost:8000/docs`

### Endpoints

#### Search API (`/api/search`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search/books` | Search books with filters |
| GET | `/api/search/books/{qid}` | Get book by QID |
| GET | `/api/search/authors/{qid}` | Get author by QID |

**Search Books Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `country` | string | Author nationality QID | `Q30` (USA) |
| `genre` | string | Genre QID | `Q1422746` (Magic Realism) |
| `year_start` | int | Start of year range | `1920` |
| `year_end` | int | End of year range | `1940` |
| `limit` | int | Max results (1-200) | `50` |
| `offset` | int | Pagination offset | `0` |

**Common QIDs:**
- Countries: Q30 (USA), Q142 (France), Q145 (UK), Q96 (Mexico), Q414 (Argentina)
- Genres: Q1422746 (Magic Realism), Q8261 (Novel), Q482 (Poetry)

#### Graph API (`/api/graph`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/graph/network` | Build author relationship network |
| GET | `/api/graph/author/{qid}/books` | Get books by author |

**Network Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `authors` | list[string] | Author QIDs (required) | - |
| `depth` | int | Relationship depth (1-3) | `2` |
| `include_coauthorship` | bool | Include co-authorship edges | `false` |
| `include_movements` | bool | Include movement connections | `true` |

**Relationship Types (Wikidata Properties):**
- `P737`: influenced by
- `P1066`: student of
- `P135`: movement membership

#### Geography API (`/api/geo`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/geo/locations` | Get geographic points for map |
| GET | `/api/geo/author/{qid}/locations` | Get all locations for author |

**Layer Types:**
- `birthplaces`: Author birth locations (P19 + P625)
- `deathplaces`: Author death locations (P20 + P625)
- `publications`: Book publication places (P291 + P625)
- `settings`: Narrative/story locations (P840 + P625)

#### Recommendations API (`/api/recommendations`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/recommendations/similar/{qid}` | Find similar authors |

Uses Jaccard similarity on: movements (P135), genres (P136), awards (P166), time period.

---

## 🔧 Backend Services

### WikidataClient (`wikidata_client.py`)
Robust SPARQL client for the Wikidata Query Service.

**Features:**
- Automatic retry with exponential backoff for 503/429 errors
- Query timeout handling (60s Wikidata limit)
- Cache key generation for consistent caching
- Proper User-Agent header per Wikidata guidelines

**Error Handling:**
- `WikidataTimeoutError`: Query exceeded 60s timeout
- `WikidataRateLimitError`: 429 Too Many Requests (retried)
- `WikidataServiceError`: 503 Service Unavailable (retried)

### CacheService (`cache_service.py`)
Redis-based caching with Cache-Aside pattern.

**TTL Strategy:**
| Data Type | TTL | Use Case |
|-----------|-----|----------|
| Static data | 7 days | Historical author/book data |
| Search results | 24 hours | Dynamic search queries |
| Warm cache | 30 days | Pre-cached popular queries |

**Features:**
- Graceful degradation if Redis unavailable
- JSON serialization for complex objects
- Cache key generation for consistent lookups

### SearchService (`search_service.py`)
Handles book and author search queries.

**Features:**
- Dynamic SPARQL query building via Jinja2 templates
- Multi-filter support (country, genre, year range)
- Pagination with configurable limits

### GraphService (`graph_service.py`)
Builds author relationship networks for D3.js visualization.

**Features:**
- Multi-hop relationship queries (1-3 depth)
- Centrality calculation using NetworkX (betweenness centrality)
- Edge type mapping for styling

**Node Types:** `author`, `book`, `movement`, `location`
**Edge Types:** `influenced_by`, `student_of`, `authored`, `member_of`

### GeoService (`geo_service.py`)
Processes geographic data for map visualization.

**Features:**
- Resolves P625 coordinates for multiple contexts
- Server-side clustering when points > 1000
- Multiple layer support

### RecommendationService (`recommendation_service.py`)
Author recommendations using Jaccard similarity.

**Similarity Factors:**
- Literary movements (P135)
- Genres of works (P136)
- Awards received (P166)
- Time period (birth decade)

---

## 🎨 Frontend Components

### ForceGraph (`ForceGraph.tsx`)
D3.js force-directed graph for author influence networks.
- Nodes colored by type (author/movement)
- Node size based on centrality score
- Interactive: drag, zoom, click for details

### BooksForceGraph (`BooksForceGraph.tsx`)
Specialized graph showing author-book relationships.
- Two-mode network (authors ↔ books)
- Useful for exploring an author's works

### MapView (`MapView.tsx`)
React-Leaflet map with dual-layer visualization.
- **Red pins**: Author birthplaces
- **Blue pins**: Narrative locations (story settings)
- Supports clustering for large datasets

### Timeline (`Timeline.tsx`)
Interactive timeline of literary publications.
- Filterable by decade
- Click events to explore specific works

### FacetedSearchSidebar (`FacetedSearchSidebar.tsx`)
Search filter panel with preset configurations.
- Country selector (QID-based)
- Genre selector
- Year range picker
- Preset scenarios (Lost Generation, Magic Realism)

### EmptyState (`EmptyState.tsx`)
Unified loading, empty, and error states.
- Loading spinner with message
- Empty state with call-to-action
- Error display with retry option

---

## 📊 Data Models

### Book
Represents a literary work from Wikidata.

```typescript
interface Book {
    qid: string;           // Wikidata Q-identifier
    title: string;
    publication_year: number | null;
    authors: string[];     // Author names
    author_qids: string[]; // Author QIDs for linking
    genre: string | null;
    publication_place: Location | null;
    narrative_locations: Location[];  // P840 story settings
    language: string | null;
}
```

### Author
Represents an author with biographical data.

```typescript
interface Author {
    qid: string;
    name: string;
    birth_place: Location | null;
    death_place: Location | null;
    nationality: string;
    movements: string[];       // Literary movements
    influenced_by: string[];   // P737 influences
    notable_works: string[];
}
```

### GraphData
Network data structure for D3.js visualization.

```typescript
interface GraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
    node_count: number;
    edge_count: number;
    central_nodes: string[];  // Most influential nodes
}
```

### GeoResponse
Geographic data with optional clustering.

```typescript
interface GeoResponse {
    layer: GeoLayerType;
    points: GeoPoint[];
    clusters: GeoCluster[];
    total_count: number;
    is_clustered: boolean;
}
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WIKIDATA_ENDPOINT` | Wikidata SPARQL endpoint | `https://query.wikidata.org/sparql` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `CACHE_TTL_STATIC` | TTL for static data (seconds) | `604800` (7 days) |
| `CACHE_TTL_SEARCH` | TTL for search results | `86400` (24 hours) |
| `DEFAULT_QUERY_LIMIT` | Default result limit | `100` |
| `MAX_QUERY_LIMIT` | Maximum result limit | `500` |
| `QUERY_TIMEOUT` | SPARQL query timeout | `55` seconds |
| `MAX_RETRIES` | Max retry attempts | `3` |
| `GEO_CLUSTER_THRESHOLD` | Point count for clustering | `1000` |

### Pydantic Settings (`config.py`)
Configuration is managed via Pydantic Settings with `.env` file support:

```python
class Settings(BaseSettings):
    wikidata_endpoint: str = "https://query.wikidata.org/sparql"
    redis_url: str = "redis://localhost:6379"
    cache_ttl_static: int = 604800
    # ... more settings
```

---

## 👩‍💻 Development Guide

### Adding a New Endpoint

1. **Create/update the router** in `backend/app/routers/`
2. **Create/update the service** in `backend/app/services/`
3. **Add SPARQL template** (if needed) in `backend/app/sparql/templates/`
4. **Update models** in `backend/app/models/` (if needed)
5. **Add frontend API client** in `frontend/src/api/client.ts`
6. **Create React Query hook** in `frontend/src/api/hooks.ts`

### Adding a New SPARQL Query

1. Create template in `backend/app/sparql/templates/your_query.sparql`
2. Use Jinja2 syntax for dynamic parameters:
   ```sparql
   SELECT ?item WHERE {
       {% if country_qid %}
       ?author wdt:P27 wd:{{ country_qid }}.
       {% endif %}
   }
   ```
3. Render in service using `render_sparql("your_query.sparql", **params)`

### Testing Wikidata Queries

Test queries directly at: https://query.wikidata.org/

### Debugging Cache

```bash
# Connect to Redis container
docker exec -it bir-redis-1 redis-cli

# List all keys
KEYS *

# Get specific key
GET <key>

# Clear cache
FLUSHALL
```

---

## 📚 Additional Documentation

| Document | Description |
|----------|-------------|
| [Backend README](./backend/README.md) | Backend service architecture and usage |
| [Frontend README](./frontend/README.md) | Frontend components and setup |
| [API Reference](./docs/API_REFERENCE.md) | Complete REST API documentation |
| [Wikidata Guide](./docs/WIKIDATA_GUIDE.md) | SPARQL queries and Wikidata integration |
| [Architecture Decisions](./docs/ARCHITECTURE.md) | ADRs explaining design choices |
| [Contributing Guide](./CONTRIBUTING.md) | How to contribute to the project |

---

## 📄 License

This project is developed for educational purposes as part of the "Big Data Retriever" assignment.

---