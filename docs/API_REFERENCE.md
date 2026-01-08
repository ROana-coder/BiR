# Literature Explorer API Reference

Complete API documentation for the Literature Explorer backend.

## Base URL

```
http://localhost:8000/api
```

## Authentication

No authentication required. All endpoints are public.

## Rate Limiting

The backend implements exponential backoff when Wikidata rate limits are hit. Clients should handle 504 (Gateway Timeout) and 503 (Service Unavailable) errors gracefully.

---

## Search Endpoints

### GET /api/search/books

Search for books with optional filters.

**Parameters:**

| Name | Type | In | Required | Description |
|------|------|------|----------|-------------|
| country | string | query | No | Author nationality QID (e.g., `Q30` for USA) |
| genre | string | query | No | Genre QID (e.g., `Q1422746` for Magic Realism) |
| location | string | query | No | Author birthplace/residence QID |
| year_start | integer | query | No | Start of publication year range (1-2030) |
| year_end | integer | query | No | End of publication year range (1-2030) |
| limit | integer | query | No | Maximum results (1-200, default: 50) |
| offset | integer | query | No | Pagination offset (default: 0) |

**Example Request:**
```bash
curl "http://localhost:8000/api/search/books?country=Q30&year_start=1920&year_end=1940&limit=20"
```

**Example Response:**
```json
[
  {
    "qid": "Q173169",
    "title": "The Old Man and the Sea",
    "publication_date": "1952-09-01",
    "publication_year": 1952,
    "authors": ["Ernest Hemingway"],
    "author_qids": ["Q23434"],
    "genre": "novella",
    "genre_qid": "Q149537",
    "genres": ["novella", "literary fiction"],
    "genre_qids": ["Q149537", "Q1196311"],
    "publication_place": {
      "qid": "Q60",
      "name": "New York City",
      "coordinates": [40.7128, -74.006],
      "country": "United States"
    },
    "narrative_locations": [],
    "language": "English",
    "language_qid": "Q1860",
    "awards": ["Pulitzer Prize for Fiction"],
    "award_qids": ["Q627975"]
  }
]
```

**Error Responses:**
- `400 Bad Request`: Invalid QID format
- `504 Gateway Timeout`: Query timeout (try narrower filters)

---

### GET /api/search/books/{qid}

Get a specific book by its QID.

**Parameters:**

| Name | Type | In | Required | Description |
|------|------|------|----------|-------------|
| qid | string | path | Yes | Wikidata QID (e.g., `Q173169`) |

**Example Request:**
```bash
curl "http://localhost:8000/api/search/books/Q173169"
```

---

### GET /api/search/authors/{qid}

Get a specific author by their QID.

**Parameters:**

| Name | Type | In | Required | Description |
|------|------|------|----------|-------------|
| qid | string | path | Yes | Wikidata QID (e.g., `Q23434`) |

**Example Response:**
```json
{
  "qid": "Q23434",
  "name": "Ernest Hemingway",
  "description": "American novelist and journalist",
  "image_url": "https://upload.wikimedia.org/...",
  "birth_date": "1899-07-21",
  "death_date": "1961-07-02",
  "birth_place": {
    "qid": "Q494413",
    "name": "Oak Park",
    "coordinates": [41.885, -87.787],
    "country": "United States"
  },
  "death_place": {
    "qid": "Q35733",
    "name": "Ketchum",
    "coordinates": [43.681, -114.363],
    "country": "United States"
  },
  "nationality": "American",
  "nationality_qid": "Q30",
  "movements": ["Lost Generation", "Modernism"],
  "movement_qids": ["Q213047", "Q37068"],
  "notable_works": ["The Old Man and the Sea", "A Farewell to Arms"],
  "notable_work_qids": ["Q173169", "Q47677"],
  "influenced_by": ["Gertrude Stein", "Ezra Pound"],
  "influenced_by_qids": ["Q188385", "Q163366"],
  "occupations": ["writer", "journalist"]
}
```

---

## Graph Endpoints

### GET /api/graph/network

Build an author relationship network for D3.js visualization.

**Parameters:**

| Name | Type | In | Required | Description |
|------|------|------|----------|-------------|
| authors | array[string] | query | Yes | Author QIDs to build network from |
| depth | integer | query | No | Relationship depth/hops (1-3, default: 2) |
| include_coauthorship | boolean | query | No | Include co-authorship edges (default: false) |
| include_movements | boolean | query | No | Include same-movement connections (default: true) |

**Example Request:**
```bash
curl "http://localhost:8000/api/graph/network?authors=Q23434&authors=Q188385&depth=2"
```

**Example Response:**
```json
{
  "nodes": [
    {
      "id": "Q23434",
      "label": "Ernest Hemingway",
      "type": "author",
      "metadata": {
        "birth_year": 1899,
        "nationality": "American"
      },
      "centrality": 0.42,
      "degree": 8
    },
    {
      "id": "Q188385",
      "label": "Gertrude Stein",
      "type": "author",
      "metadata": {},
      "centrality": 0.65,
      "degree": 12
    }
  ],
  "edges": [
    {
      "source": "Q23434",
      "target": "Q188385",
      "type": "influenced_by",
      "weight": 1.0,
      "label": "influenced by"
    }
  ],
  "node_count": 2,
  "edge_count": 1,
  "central_nodes": ["Q188385", "Q23434"]
}
```

**Relationship Types:**
- `influenced_by`: P737 - Author was intellectually influenced
- `influenced`: Inverse of P737 - Author influenced others
- `student_of`: P1066 - Mentor/student relationship
- `teacher_of`: Inverse of P1066
- `coauthor`: Shared authorship on works
- `same_movement`: Shared literary movement (P135)

**Node Types:**
- `author`: Writer/literary figure
- `book`: Literary work
- `movement`: Literary movement
- `location`: Geographic place

---

### GET /api/graph/author/{qid}/books

Get all books authored by a specific author.

**Parameters:**

| Name | Type | In | Required | Description |
|------|------|------|----------|-------------|
| qid | string | path | Yes | Author QID |

**Example Request:**
```bash
curl "http://localhost:8000/api/graph/author/Q23434/books"
```

---

## Geography Endpoints

### GET /api/geo/locations

Get geographic coordinates for map visualization.

**Parameters:**

| Name | Type | In | Required | Description |
|------|------|------|----------|-------------|
| layer | string | query | Yes | Geographic layer type |
| authors | array[string] | query | Conditional | Author QIDs (required for birthplaces/deathplaces) |
| books | array[string] | query | Conditional | Book QIDs (for publications/settings) |
| cluster | boolean | query | No | Enable server-side clustering (default: true) |

**Layer Types:**
- `birthplaces`: Author birth locations (P19 + P625)
- `deathplaces`: Author death locations (P20 + P625)
- `publications`: Book publication places (P291 + P625)
- `settings`: Narrative/story locations (P840 + P625)

**Example Request:**
```bash
curl "http://localhost:8000/api/geo/locations?layer=birthplaces&authors=Q23434&authors=Q188385"
```

**Example Response:**
```json
{
  "layer": "birthplaces",
  "points": [
    {
      "qid": "Q494413",
      "name": "Oak Park",
      "latitude": 41.885,
      "longitude": -87.787,
      "layer": "birthplaces",
      "entity_qid": "Q23434",
      "entity_name": "Ernest Hemingway",
      "entity_type": "author",
      "year": 1899
    }
  ],
  "clusters": [],
  "total_count": 1,
  "is_clustered": false
}
```

**Clustered Response (when points > 1000):**
```json
{
  "layer": "birthplaces",
  "points": [],
  "clusters": [
    {
      "center_latitude": 48.856,
      "center_longitude": 2.352,
      "point_count": 42,
      "layer": "birthplaces",
      "sample_points": [...],
      "bounds": [48.8, 2.2, 48.9, 2.4]
    }
  ],
  "total_count": 42,
  "is_clustered": true
}
```

---

### GET /api/geo/author/{qid}/locations

Get all geographic locations associated with an author.

**Parameters:**

| Name | Type | In | Required | Description |
|------|------|------|----------|-------------|
| qid | string | path | Yes | Author QID |

**Returns:** Object with keys for each layer type containing GeoResponse data.

---

## Recommendation Endpoints

### GET /api/recommendations/similar/{qid}

Find authors similar to the given author using Jaccard similarity.

**Parameters:**

| Name | Type | In | Required | Description |
|------|------|------|----------|-------------|
| qid | string | path | Yes | Author QID |
| limit | integer | query | No | Maximum results (default: 10) |

**Similarity Factors:**
- Literary movements (P135)
- Genres of works (P136)
- Awards received (P166)
- Time period (birth decade)

**Example Request:**
```bash
curl "http://localhost:8000/api/recommendations/similar/Q23434?limit=5"
```

**Example Response:**
```json
[
  {
    "qid": "Q188385",
    "name": "Gertrude Stein",
    "similarity": 0.65,
    "shared_movements": ["Lost Generation", "Modernism"],
    "shared_genres": ["autobiography"]
  },
  {
    "qid": "Q229466",
    "name": "F. Scott Fitzgerald",
    "similarity": 0.58,
    "shared_movements": ["Lost Generation"],
    "shared_genres": ["novel"]
  }
]
```

---

## Common Wikidata QIDs

### Countries (P27)

| QID | Country |
|-----|---------|
| Q30 | United States |
| Q142 | France |
| Q145 | United Kingdom |
| Q183 | Germany |
| Q96 | Mexico |
| Q414 | Argentina |
| Q17 | Japan |
| Q668 | India |
| Q155 | Brazil |
| Q159 | Russia |

### Genres (P136)

| QID | Genre |
|-----|-------|
| Q8261 | Novel |
| Q1422746 | Magic Realism |
| Q149537 | Novella |
| Q49084 | Short Story |
| Q482 | Poetry |
| Q1196311 | Literary Fiction |
| Q208505 | Autobiography |
| Q192782 | Detective Fiction |
| Q11631 | Science Fiction |
| Q14028 | Horror |

### Literary Movements (P135)

| QID | Movement |
|-----|----------|
| Q213047 | Lost Generation |
| Q37068 | Modernism |
| Q2658555 | Magic Realism |
| Q180089 | Romanticism |
| Q160772 | Naturalism |
| Q170583 | Surrealism |
| Q167312 | Existentialism |

### Notable Authors

| QID | Author |
|-----|--------|
| Q23434 | Ernest Hemingway |
| Q188385 | Gertrude Stein |
| Q229466 | F. Scott Fitzgerald |
| Q163366 | Ezra Pound |
| Q5879 | James Joyce |
| Q161687 | Gabriel García Márquez |
| Q170509 | Jorge Luis Borges |

---

## Error Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 200 | Success | Request completed |
| 400 | Bad Request | Invalid QID format, missing required params |
| 404 | Not Found | Entity not found in Wikidata |
| 500 | Internal Error | Unexpected server error |
| 503 | Service Unavailable | Wikidata temporarily down |
| 504 | Gateway Timeout | Query exceeded 60s timeout |

---

## Tips for Efficient Queries

1. **Use filters**: More filters = faster queries (smaller result sets)
2. **Limit results**: Start with `limit=50`, increase if needed
3. **Use year ranges**: Narrow time periods reduce query complexity
4. **Retry on 503**: Wikidata has occasional outages, retry after delay
5. **Cache responses**: Results are stable for historical data
