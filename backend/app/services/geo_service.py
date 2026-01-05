"""Geo service for map visualization."""

import logging
from statistics import mean

from app.config import get_settings
from app.models.geo import GeoPoint, GeoCluster, GeoResponse, GeoLayerType
from app.services.wikidata_client import WikidataClient
from app.services.cache_service import CacheService
from app.sparql.template_loader import render_sparql

logger = logging.getLogger(__name__)


class GeoService:
    """Service for geographic data and map visualization.
    
    Features:
        - Resolves P625 coordinates for multiple contexts
        - Server-side clustering for performance
        - Multiple layer support (birthplaces, publications, settings)
    """
    
    def __init__(
        self,
        wikidata_client: WikidataClient,
        cache_service: CacheService,
    ):
        self.client = wikidata_client
        self.cache = cache_service
        self.settings = get_settings()
    
    async def get_locations(
        self,
        layer: GeoLayerType,
        author_qids: list[str] | None = None,
        book_qids: list[str] | None = None,
        cluster: bool = True,
    ) -> GeoResponse:
        """Get geographic points for a specific layer.
        
        Args:
            layer: Type of geographic layer
            author_qids: Filter by specific authors
            book_qids: Filter by specific books
            cluster: Enable clustering when points > threshold
            
        Returns:
            GeoResponse with points or clusters
        """
        # Generate cache key
        cache_key = WikidataClient.generate_cache_key(
            "geo_locations",
            layer=layer.value,
            authors=",".join(sorted(author_qids or [])),
            books=",".join(sorted(book_qids or [])),
        )
        
        # Try cache
        cached = await self.cache.get(cache_key)
        if cached:
            return GeoResponse(**cached)
        
        # Render SPARQL query
        query = render_sparql(
            "geo_locations.sparql",
            layer=layer.value,
            author_qids=author_qids,
            book_qids=book_qids,
            limit=2000,
        )
        
        # Execute query
        results = await self.client.execute_query(query)
        
        # Parse results into GeoPoints
        points = self._parse_geo_results(results, layer)
        
        # Apply clustering if needed
        response = self._build_response(points, layer, cluster)
        
        # Cache result
        await self.cache.set(
            cache_key,
            response.model_dump(),
            ttl_seconds=self.settings.cache_ttl_static,
        )
        
        return response
    
    def _parse_geo_results(
        self,
        results: list[dict],
        layer: GeoLayerType,
    ) -> list[GeoPoint]:
        """Parse SPARQL results into GeoPoint models."""
        points = []
        seen = set()  # Avoid duplicate points
        
        for row in results:
            location_qid = row.get("location", "")
            lat = row.get("lat")
            lon = row.get("lon")
            
            if not location_qid or not lat or not lon:
                continue
            
            try:
                lat_float = float(lat)
                lon_float = float(lon)
            except (ValueError, TypeError):
                continue
            
            # Unique key to avoid duplicates
            key = (location_qid, row.get("entity", ""))
            if key in seen:
                continue
            seen.add(key)
            
            # Parse year
            year = None
            if "year" in row:
                try:
                    year = int(row["year"])
                except (ValueError, TypeError):
                    pass
            
            point = GeoPoint(
                qid=location_qid,
                name=row.get("locationLabel", "Unknown"),
                latitude=lat_float,
                longitude=lon_float,
                layer=layer,
                entity_qid=row.get("entity"),
                entity_name=row.get("entityLabel"),
                entity_type=row.get("entityType"),
                year=year,
            )
            points.append(point)
        
        return points
    
    def _build_response(
        self,
        points: list[GeoPoint],
        layer: GeoLayerType,
        cluster: bool,
    ) -> GeoResponse:
        """Build response with optional clustering."""
        threshold = self.settings.geo_cluster_threshold
        
        if not cluster or len(points) <= threshold:
            return GeoResponse(
                points=points,
                clusters=[],
                total_count=len(points),
                is_clustered=False,
                layer=layer,
            )
        
        # Apply simple grid-based clustering
        clusters = self._cluster_points(points, layer)
        
        return GeoResponse(
            points=[],  # Don't send individual points when clustered
            clusters=clusters,
            total_count=len(points),
            is_clustered=True,
            layer=layer,
        )
    
    def _cluster_points(
        self,
        points: list[GeoPoint],
        layer: GeoLayerType,
        grid_size: float = 2.0,  # Degrees
    ) -> list[GeoCluster]:
        """Simple grid-based clustering for performance.
        
        Args:
            points: List of GeoPoints to cluster
            layer: Layer type
            grid_size: Grid cell size in degrees
            
        Returns:
            List of GeoCluster objects
        """
        # Group points by grid cell
        grid: dict[tuple[int, int], list[GeoPoint]] = {}
        
        for point in points:
            # Calculate grid cell
            cell_x = int(point.longitude / grid_size)
            cell_y = int(point.latitude / grid_size)
            cell_key = (cell_x, cell_y)
            
            if cell_key not in grid:
                grid[cell_key] = []
            grid[cell_key].append(point)
        
        # Create clusters from grid cells
        clusters = []
        
        for cell_key, cell_points in grid.items():
            if len(cell_points) < 2:
                # Don't cluster single points
                continue
            
            # Calculate center
            center_lat = mean(p.latitude for p in cell_points)
            center_lon = mean(p.longitude for p in cell_points)
            
            # Calculate bounds
            min_lat = min(p.latitude for p in cell_points)
            max_lat = max(p.latitude for p in cell_points)
            min_lon = min(p.longitude for p in cell_points)
            max_lon = max(p.longitude for p in cell_points)
            
            # Sample points for popup
            sample = cell_points[:5]
            
            cluster = GeoCluster(
                center_latitude=center_lat,
                center_longitude=center_lon,
                point_count=len(cell_points),
                layer=layer,
                sample_points=sample,
                bounds=(min_lat, min_lon, max_lat, max_lon),
            )
            clusters.append(cluster)
        
        return clusters
    
    async def get_all_author_locations(
        self,
        author_qids: list[str],
    ) -> dict[str, GeoResponse]:
        """Get all location layers for a set of authors.
        
        Returns dict with keys: 'birthplaces', 'deathplaces'
        """
        result = {}
        
        for layer in [GeoLayerType.BIRTHPLACES, GeoLayerType.DEATHPLACES]:
            response = await self.get_locations(
                layer=layer,
                author_qids=author_qids,
            )
            result[layer.value] = response
        
        return result
