# Architecture Decision Records

This document captures key architectural decisions made during the development of Literature Explorer.

---

## ADR-001: Use Wikidata as Primary Data Source

**Status:** Accepted

**Context:**
We need a comprehensive, freely accessible data source for literary information including authors, books, movements, and geographic data.

**Decision:**
Use Wikidata's SPARQL endpoint as the primary data source.

**Consequences:**
- ✅ Access to millions of entities with rich relationships
- ✅ Free and open access
- ✅ Structured data with standardized properties
- ✅ Geographic coordinates available for locations
- ⚠️ 60-second query timeout limit
- ⚠️ Rate limiting during peak usage
- ⚠️ Data quality varies by entity

---

## ADR-002: Cache-Aside Pattern with Redis

**Status:** Accepted

**Context:**
Wikidata has rate limits and query timeouts. Repeated queries for the same data waste resources and impact user experience.

**Decision:**
Implement Cache-Aside pattern using Redis:
1. Check cache before querying Wikidata
2. On cache miss, query Wikidata and store result
3. Return cached data on subsequent requests

**TTL Strategy:**
| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Historical data | 7 days | Author/book data rarely changes |
| Search results | 24 hours | Balance freshness with performance |
| Warm cache | 30 days | Pre-cached popular queries |

**Consequences:**
- ✅ Dramatically improved response times
- ✅ Reduced load on Wikidata
- ✅ Resilience during Wikidata outages
- ⚠️ Additional infrastructure (Redis)
- ⚠️ Potential stale data (acceptable for historical content)

---

## ADR-003: FastAPI for Backend

**Status:** Accepted

**Context:**
Need a modern Python web framework that supports async operations, automatic API documentation, and type validation.

**Decision:**
Use FastAPI with Pydantic for the backend API.

**Consequences:**
- ✅ Native async/await support
- ✅ Automatic OpenAPI documentation
- ✅ Pydantic validation for request/response
- ✅ High performance (Starlette/Uvicorn)
- ✅ Dependency injection system
- ⚠️ Requires Python 3.9+

---

## ADR-004: SPARQL Template System (Jinja2)

**Status:** Accepted

**Context:**
SPARQL queries need to be dynamic based on user filters, but string concatenation is error-prone and hard to maintain.

**Decision:**
Use Jinja2 templates for SPARQL query generation.

**Example:**
```sparql
{% if country_qid %}
?author wdt:P27 wd:{{ country_qid }}.
{% endif %}
```

**Consequences:**
- ✅ Clean separation of query logic
- ✅ Easy to test individual templates
- ✅ Familiar syntax for developers
- ✅ Conditional clauses without string manipulation
- ⚠️ Need to disable HTML escaping for SPARQL

---

## ADR-005: D3.js for Force-Directed Graph

**Status:** Accepted

**Context:**
Need an interactive network visualization for author relationships that supports:
- Drag and zoom interactions
- Node sizing by centrality
- Edge styling by relationship type
- Click handlers for detail views

**Decision:**
Use D3.js force simulation with React integration.

**Alternatives Considered:**
- Cytoscape.js: More features but larger bundle
- vis.js: Good but less customizable
- Sigma.js: WebGL-based, overkill for our use case

**Consequences:**
- ✅ Highly customizable
- ✅ Good performance for <1000 nodes
- ✅ Wide community support
- ⚠️ Steeper learning curve
- ⚠️ Requires manual React/D3 integration

---

## ADR-006: React-Leaflet for Maps

**Status:** Accepted

**Context:**
Need a map visualization showing author birthplaces and narrative locations with clustering support.

**Decision:**
Use React-Leaflet with OpenStreetMap tiles.

**Consequences:**
- ✅ Free (OpenStreetMap)
- ✅ React-friendly API
- ✅ Built-in marker clustering
- ✅ Good mobile support
- ⚠️ Less polished than Google Maps

---

## ADR-007: TanStack Query for Data Fetching

**Status:** Accepted

**Context:**
Frontend needs to manage:
- API request caching
- Loading/error states
- Automatic refetching
- Cache invalidation

**Decision:**
Use TanStack Query (React Query) for all API interactions.

**Consequences:**
- ✅ Built-in caching with configurable stale times
- ✅ Automatic background refetching
- ✅ Request deduplication
- ✅ DevTools for debugging
- ⚠️ Additional dependency

---

## ADR-008: NetworkX for Graph Metrics

**Status:** Accepted

**Context:**
Need to calculate graph centrality metrics server-side for node sizing in visualizations.

**Decision:**
Use NetworkX to compute betweenness centrality and identify central nodes.

**Consequences:**
- ✅ Comprehensive graph algorithms
- ✅ Easy integration with Python
- ✅ Well-documented
- ⚠️ CPU-intensive for large graphs

---

## ADR-009: Jaccard Similarity for Recommendations

**Status:** Accepted

**Context:**
Need to recommend similar authors based on shared characteristics.

**Decision:**
Use Jaccard similarity coefficient on feature sets:
- Literary movements (P135)
- Genres (P136)
- Awards (P166)
- Birth decade (derived from P569)

**Formula:**
```
J(A,B) = |A ∩ B| / |A ∪ B|
```

**Consequences:**
- ✅ Simple and interpretable
- ✅ Works well with categorical data
- ✅ No training required
- ⚠️ Limited to explicit features (no latent factors)

---

## ADR-010: Docker Compose for Development

**Status:** Accepted

**Context:**
Need consistent development environment with multiple services (backend, frontend, Redis).

**Decision:**
Use Docker Compose for local development with hot-reload volumes.

**Consequences:**
- ✅ Consistent environments
- ✅ Easy onboarding
- ✅ Service orchestration
- ⚠️ Requires Docker installation
- ⚠️ Slower than native for some operations

---

## ADR-011: Server-Side Geo Clustering

**Status:** Accepted

**Context:**
Large numbers of map markers (>1000) cause frontend DOM performance issues.

**Decision:**
Implement server-side clustering when point count exceeds threshold (1000).

**Algorithm:**
Simple grid-based clustering with representative sample points.

**Consequences:**
- ✅ Consistent frontend performance
- ✅ Reduced network payload
- ⚠️ Less precise than client-side clustering
- ⚠️ Additional backend complexity
