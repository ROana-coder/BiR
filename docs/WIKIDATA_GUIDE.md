# Wikidata Integration Guide

This document explains how Literature Explorer integrates with Wikidata's SPARQL endpoint.

## Overview

Literature Explorer uses [Wikidata](https://www.wikidata.org/) as its primary data source. Wikidata is a free, collaborative knowledge base that provides structured data about millions of entities, including authors, books, and literary movements.

## SPARQL Endpoint

**Endpoint URL:** `https://query.wikidata.org/sparql`

**Query Interface:** https://query.wikidata.org/

## Key Wikidata Properties

### Entity Types (P31 - instance of)

| QID | Entity Type |
|-----|-------------|
| Q5 | Human |
| Q571 | Book |
| Q7725634 | Literary Work |
| Q47461344 | Written Work |
| Q36279 | Literary Movement |

### Author Properties

| Property | Description | Example |
|----------|-------------|---------|
| P27 | Country of citizenship | Q30 (USA) |
| P19 | Place of birth | Q90 (Paris) |
| P20 | Place of death | Q60 (NYC) |
| P569 | Date of birth | 1899-07-21 |
| P570 | Date of death | 1961-07-02 |
| P135 | Movement | Q213047 (Lost Generation) |
| P106 | Occupation | Q36180 (writer) |
| P737 | Influenced by | Q5879 (Joyce) |
| P1066 | Student of | Q188385 (Stein) |
| P800 | Notable work | Q173169 (Old Man and the Sea) |
| P18 | Image | URL to Commons image |

### Book Properties

| Property | Description | Example |
|----------|-------------|---------|
| P31 | Instance of | Q571 (book) |
| P50 | Author | Q23434 (Hemingway) |
| P577 | Publication date | 1952-09-01 |
| P136 | Genre | Q149537 (novella) |
| P291 | Place of publication | Q60 (NYC) |
| P840 | Narrative location | Q1297 (Cuba) |
| P407 | Language of work | Q1860 (English) |
| P166 | Award received | Q627975 (Pulitzer) |

### Geographic Properties

| Property | Description |
|----------|-------------|
| P625 | Coordinate location |
| P17 | Country |
| P131 | Located in administrative entity |

## SPARQL Query Examples

### 1. Search Books by Author Nationality

```sparql
SELECT ?book ?bookLabel ?authorLabel ?pubDate
WHERE {
  ?book wdt:P31 wd:Q571.          # instance of book
  ?book wdt:P50 ?author.          # has author
  ?author wdt:P27 wd:Q30.         # author is American (Q30 = USA)
  ?book wdt:P577 ?pubDate.        # publication date
  
  FILTER(YEAR(?pubDate) >= 1920 && YEAR(?pubDate) <= 1940)
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
```

### 2. Author Influence Network

```sparql
SELECT ?source ?sourceLabel ?target ?targetLabel
WHERE {
  VALUES ?source { wd:Q23434 wd:Q188385 }  # Hemingway, Stein
  
  ?source wdt:P737 ?target.        # influenced by
  ?target wdt:P31 wd:Q5.           # target is human
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

### 3. Author Birthplaces with Coordinates

```sparql
SELECT ?author ?authorLabel ?birthPlace ?birthPlaceLabel ?lat ?lon
WHERE {
  VALUES ?author { wd:Q23434 wd:Q188385 }
  
  ?author wdt:P19 ?birthPlace.     # place of birth
  ?birthPlace wdt:P625 ?coord.     # coordinate location
  
  BIND(geof:latitude(?coord) AS ?lat)
  BIND(geof:longitude(?coord) AS ?lon)
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

### 4. Books by Genre

```sparql
SELECT ?book ?bookLabel ?authorLabel
WHERE {
  ?book wdt:P31 wd:Q571.           # instance of book
  ?book wdt:P136 wd:Q1422746.      # genre: magic realism
  ?book wdt:P50 ?author.           # has author
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 50
```

### 5. Narrative Locations (Story Settings)

```sparql
SELECT ?book ?bookLabel ?location ?locationLabel ?lat ?lon
WHERE {
  ?book wdt:P31 wd:Q571.           # instance of book
  ?book wdt:P840 ?location.        # narrative location
  ?location wdt:P625 ?coord.       # has coordinates
  
  BIND(geof:latitude(?coord) AS ?lat)
  BIND(geof:longitude(?coord) AS ?lon)
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
```

## Query Optimization Tips

### 1. Use Subqueries for Filtering

Instead of filtering in the main query, use subqueries:

```sparql
SELECT ?book ?bookLabel
WHERE {
  {
    SELECT ?book WHERE {
      ?book wdt:P31 wd:Q571.
      ?book wdt:P50 ?author.
      ?author wdt:P27 wd:Q30.
    }
    LIMIT 100  # Apply limit early
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

### 2. Disable Query Optimizer for Complex Queries

```sparql
SELECT ?item WHERE {
  hint:Query hint:optimizer "None".
  # ... complex query
}
```

### 3. Use VALUES for Known Entities

```sparql
# Instead of:
?author wdt:P27 wd:Q30.
?author wdt:P27 wd:Q142.

# Use:
VALUES ?country { wd:Q30 wd:Q142 }
?author wdt:P27 ?country.
```

### 4. Aggregate with GROUP_CONCAT

```sparql
SELECT ?book ?bookLabel (GROUP_CONCAT(DISTINCT ?genreLabel; separator=", ") AS ?genres)
WHERE {
  ?book wdt:P31 wd:Q571.
  OPTIONAL { 
    ?book wdt:P136 ?genre. 
    ?genre rdfs:label ?genreLabel. 
    FILTER(LANG(?genreLabel) = "en") 
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
GROUP BY ?book ?bookLabel
```

## Rate Limits and Best Practices

### Wikidata Rate Limits

- **Query timeout:** 60 seconds
- **Concurrent requests:** Limited (exact number not published)
- **Response codes:**
  - 429: Too Many Requests
  - 503: Service Unavailable

### Our Mitigation Strategies

1. **Exponential Backoff Retry**
   ```python
   @retry(
       retry=retry_if_exception_type((WikidataServiceError, WikidataRateLimitError)),
       stop=stop_after_attempt(3),
       wait=wait_exponential(multiplier=1, min=1, max=10),
   )
   async def execute_query(self, query: str):
       ...
   ```

2. **Redis Caching**
   - Static data cached for 7 days
   - Search results cached for 24 hours
   - Cache key based on query hash

3. **Query Limits**
   - Default limit: 100 results
   - Maximum limit: 500 results
   - Query timeout: 55 seconds (leave margin for 60s limit)

4. **User-Agent Header**
   ```python
   USER_AGENT = "LiteratureExplorer/1.0 (contact@example.com) httpx/0.26"
   ```

## Template System

We use Jinja2 templates for dynamic SPARQL generation:

### Template Location
`backend/app/sparql/templates/`

### Template Syntax

```sparql
{# Comment #}

{% if country_qid %}
?author wdt:P27 wd:{{ country_qid }}.
{% endif %}

{% for qid in author_qids %}
wd:{{ qid }}
{% endfor %}

LIMIT {{ limit | default(50) }}
```

### Usage

```python
from app.sparql.template_loader import render_sparql

query = render_sparql(
    "search_books.sparql",
    country_qid="Q30",
    year_start=1920,
    limit=100
)
```

## Testing Queries

1. **Wikidata Query Service:** https://query.wikidata.org/
2. **Test with smaller limits first**
3. **Check query timeout before production use**

## Common Issues

### 1. Query Timeout

**Cause:** Query too complex or result set too large
**Solution:** Add more filters, reduce LIMIT, use subqueries

### 2. Missing Labels

**Cause:** Entity doesn't have English label
**Solution:** Use multi-language fallback:
```sparql
SERVICE wikibase:label { bd:serviceParam wikibase:language "en,auto,es,fr,de". }
```

### 3. Duplicate Results

**Cause:** Multiple values for a property
**Solution:** Use `DISTINCT` or `GROUP BY`:
```sparql
SELECT DISTINCT ?book ?bookLabel
```

### 4. NULL Coordinates

**Cause:** Location doesn't have P625 property
**Solution:** Filter for coordinates:
```sparql
?location wdt:P625 ?coord.  # Only locations with coordinates
```

## Resources

- [Wikidata Query Service](https://query.wikidata.org/)
- [SPARQL Tutorial](https://www.wikidata.org/wiki/Wikidata:SPARQL_tutorial)
- [Wikidata Properties](https://www.wikidata.org/wiki/Wikidata:List_of_properties)
- [Query Optimization](https://www.mediawiki.org/wiki/Wikidata_Query_Service/User_Manual#Query_optimization)
