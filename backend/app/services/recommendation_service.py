"""Recommendation service for finding similar authors."""

import logging
from collections import defaultdict

from sklearn.metrics import jaccard_score
import numpy as np

from app.config import get_settings
from app.models import Author
from app.services.wikidata_client import WikidataClient
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for author recommendations using similarity metrics.
    
    Features:
        - Jaccard similarity on shared properties
        - Considers: movements (P135), genres, awards (P166), era
    """
    
    def __init__(
        self,
        wikidata_client: WikidataClient,
        cache_service: CacheService,
    ):
        self.client = wikidata_client
        self.cache = cache_service
        self.settings = get_settings()
    
    async def find_similar_authors(
        self,
        author_qid: str,
        limit: int = 10,
    ) -> list[dict]:
        """Find authors similar to the given author.
        
        Uses Jaccard similarity on:
            - Literary movements (P135)
            - Genres of works (P136)
            - Awards received (P166)
            - Time period (birth decade)
        
        Args:
            author_qid: QID of the source author
            limit: Maximum similar authors to return
            
        Returns:
            List of similar authors with similarity scores
        """
        # Generate cache key
        cache_key = WikidataClient.generate_cache_key(
            "similar_authors",
            author=author_qid,
            limit=limit,
        )
        
        # Try cache
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Get source author's properties
        source_props = await self._get_author_properties(author_qid)
        
        if not source_props:
            return []
        
        # Find candidate authors sharing at least one property
        candidates = await self._find_candidates(source_props)
        
        # Calculate similarity scores
        similarities = []
        
        for candidate_qid, candidate_props in candidates.items():
            if candidate_qid == author_qid:
                continue
            
            score = self._calculate_jaccard_similarity(
                source_props,
                candidate_props,
            )
            
            if score > 0:
                similarities.append({
                    "qid": candidate_qid,
                    "name": candidate_props.get("name", "Unknown"),
                    "similarity": round(score, 3),
                    "shared_movements": list(
                        set(source_props.get("movements", [])) &
                        set(candidate_props.get("movements", []))
                    ),
                    "shared_genres": list(
                        set(source_props.get("genres", [])) &
                        set(candidate_props.get("genres", []))
                    ),
                })
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        result = similarities[:limit]
        
        # Cache result
        await self.cache.set(
            cache_key,
            result,
            ttl_seconds=self.settings.cache_ttl_search,
        )
        
        return result
    
    async def _get_author_properties(self, author_qid: str) -> dict:
        """Fetch properties for an author."""
        query = f"""
        SELECT ?authorLabel ?movement ?movementLabel ?genre ?genreLabel 
               ?award ?awardLabel ?birthYear
        WHERE {{
            BIND(wd:{author_qid} AS ?author)
            
            OPTIONAL {{ ?author wdt:P135 ?movement. }}
            OPTIONAL {{
                ?work wdt:P50 ?author.
                ?work wdt:P136 ?genre.
            }}
            OPTIONAL {{ ?author wdt:P166 ?award. }}
            OPTIONAL {{
                ?author wdt:P569 ?birthDate.
                BIND(YEAR(?birthDate) AS ?birthYear)
            }}
            
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 200
        """
        
        results = await self.client.execute_query(query)
        
        if not results:
            return {}
        
        props = {
            "name": results[0].get("authorLabel", "Unknown"),
            "movements": set(),
            "genres": set(),
            "awards": set(),
            "birth_decade": None,
        }
        
        for row in results:
            if "movement" in row:
                props["movements"].add(row["movement"])
            if "genre" in row:
                props["genres"].add(row["genre"])
            if "award" in row:
                props["awards"].add(row["award"])
            if "birthYear" in row and props["birth_decade"] is None:
                try:
                    year = int(row["birthYear"])
                    props["birth_decade"] = (year // 10) * 10
                except (ValueError, TypeError):
                    pass
        
        # Convert sets to lists for JSON serialization
        props["movements"] = list(props["movements"])
        props["genres"] = list(props["genres"])
        props["awards"] = list(props["awards"])
        
        return props
    
    async def _find_candidates(self, source_props: dict) -> dict[str, dict]:
        """Find candidate authors sharing properties with source."""
        candidates = {}
        
        # Query authors sharing movements
        movements = source_props.get("movements", [])
        if movements:
            movement_values = " ".join(f"wd:{m}" for m in movements[:5])
            query = f"""
            SELECT DISTINCT ?author ?authorLabel ?movement ?movementLabel
            WHERE {{
                VALUES ?movement {{ {movement_values} }}
                ?author wdt:P135 ?movement.
                ?author wdt:P31 wd:Q5.
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
            LIMIT 100
            """
            
            results = await self.client.execute_query(query)
            
            for row in results:
                qid = row.get("author", "")
                if qid and qid not in candidates:
                    candidates[qid] = {
                        "name": row.get("authorLabel", qid),
                        "movements": [],
                        "genres": [],
                        "awards": [],
                    }
                if qid and "movement" in row:
                    candidates[qid]["movements"].append(row["movement"])
        
        # Query authors sharing genres
        genres = source_props.get("genres", [])
        if genres:
            genre_values = " ".join(f"wd:{g}" for g in genres[:5])
            query = f"""
            SELECT DISTINCT ?author ?authorLabel ?genre ?genreLabel
            WHERE {{
                VALUES ?genre {{ {genre_values} }}
                ?work wdt:P136 ?genre.
                ?work wdt:P50 ?author.
                ?author wdt:P31 wd:Q5.
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
            LIMIT 100
            """
            
            results = await self.client.execute_query(query)
            
            for row in results:
                qid = row.get("author", "")
                if qid:
                    if qid not in candidates:
                        candidates[qid] = {
                            "name": row.get("authorLabel", qid),
                            "movements": [],
                            "genres": [],
                            "awards": [],
                        }
                    if "genre" in row:
                        candidates[qid]["genres"].append(row["genre"])
        
        return candidates
    
    def _calculate_jaccard_similarity(
        self,
        props_a: dict,
        props_b: dict,
    ) -> float:
        """Calculate Jaccard similarity between two authors' properties."""
        # Combine all properties into sets
        set_a = set()
        set_b = set()
        
        for key in ["movements", "genres", "awards"]:
            set_a.update(f"{key}:{v}" for v in props_a.get(key, []))
            set_b.update(f"{key}:{v}" for v in props_b.get(key, []))
        
        # Add birth decade if both have it
        if props_a.get("birth_decade") and props_b.get("birth_decade"):
            set_a.add(f"decade:{props_a['birth_decade']}")
            set_b.add(f"decade:{props_b['birth_decade']}")
        
        if not set_a or not set_b:
            return 0.0
        
        # Calculate Jaccard index
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        
        return intersection / union if union > 0 else 0.0
