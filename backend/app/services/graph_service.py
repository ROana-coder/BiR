"""Graph service for network visualization of author relationships."""

import logging
from collections import defaultdict

import networkx as nx

from app.config import get_settings
from app.models import GraphNode, GraphEdge, GraphData
from app.models.graph import NodeType, EdgeType
from app.services.wikidata_client import WikidataClient
from app.services.cache_service import CacheService
from app.sparql.template_loader import render_sparql

logger = logging.getLogger(__name__)


class GraphService:
    """Service for building author relationship networks.
    
    Features:
        - 2-hop relationship queries (influenced by, student of, etc.)
        - Centrality calculation using NetworkX
        - Graph metrics for visualization
    """
    
    def __init__(
        self,
        wikidata_client: WikidataClient,
        cache_service: CacheService,
    ):
        self.client = wikidata_client
        self.cache = cache_service
        self.settings = get_settings()
    
    async def get_author_network(
        self,
        author_qids: list[str],
        depth: int = 2,
        include_coauthorship: bool = False,
        include_movements: bool = True,
    ) -> GraphData:
        """Build a network graph from author relationships.
        
        Args:
            author_qids: Starting author QIDs
            depth: Relationship depth (1-3, default 2)
            include_coauthorship: Include co-authorship edges
            include_movements: Include same-movement connections
            
        Returns:
            GraphData with nodes and edges for D3.js
        """
        depth = max(1, min(depth, 3))  # Clamp 1-3
        
        # Generate cache key
        cache_key = WikidataClient.generate_cache_key(
            "author_network",
            authors=",".join(sorted(author_qids)),
            depth=depth,
            coauthor=include_coauthorship,
            movements=include_movements,
        )
        
        # Try cache
        cached = await self.cache.get(cache_key)
        if cached:
            return GraphData(**cached)
        
        # Collect all nodes and edges across hops
        all_nodes: dict[str, GraphNode] = {}
        all_edges: list[GraphEdge] = []
        current_qids = set(author_qids)
        seen_qids = set(author_qids)
        
        # Multi-hop expansion
        for hop in range(depth):
            if not current_qids:
                break
            
            # Query relationships for current batch
            query = render_sparql(
                "author_graph.sparql",
                author_qids=list(current_qids),
                include_coauthorship=include_coauthorship,
                include_movements=include_movements,
                limit=500,
            )
            
            results = await self.client.execute_query(query)
            
            next_qids = set()
            
            for row in results:
                source_qid = row.get("source", "")
                target_qid = row.get("target", "")
                rel_type = row.get("relationType", "")
                
                if not source_qid or not target_qid:
                    continue
                
                # Add nodes
                if source_qid not in all_nodes:
                    all_nodes[source_qid] = GraphNode(
                        id=source_qid,
                        label=row.get("sourceLabel", source_qid),
                        type=NodeType.AUTHOR,
                    )
                
                if target_qid not in all_nodes:
                    all_nodes[target_qid] = GraphNode(
                        id=target_qid,
                        label=row.get("targetLabel", target_qid),
                        type=NodeType.AUTHOR,
                    )
                
                # Map relationship type
                edge_type = self._map_edge_type(rel_type)
                
                # Add edge (avoid duplicates)
                edge = GraphEdge(
                    source=source_qid,
                    target=target_qid,
                    type=edge_type,
                )
                
                # Check for duplicate edges
                edge_key = (source_qid, target_qid, edge_type)
                if not any(
                    (e.source, e.target, e.type) == edge_key 
                    for e in all_edges
                ):
                    all_edges.append(edge)
                
                # Queue for next hop
                if target_qid not in seen_qids:
                    next_qids.add(target_qid)
                    seen_qids.add(target_qid)
            
            current_qids = next_qids
        
        # Calculate centrality metrics
        graph_data = self._compute_graph_metrics(
            list(all_nodes.values()),
            all_edges,
        )
        
        # Cache result
        await self.cache.set(
            cache_key,
            graph_data.model_dump(),
            ttl_seconds=self.settings.cache_ttl_static,
        )
        
        return graph_data
    
    def _map_edge_type(self, rel_type: str) -> EdgeType:
        """Map SPARQL relationship type to EdgeType enum."""
        mapping = {
            "influenced_by": EdgeType.INFLUENCED_BY,
            "influenced": EdgeType.INFLUENCED_BY,  # Will swap direction
            "student_of": EdgeType.STUDENT_OF,
            "teacher_of": EdgeType.STUDENT_OF,  # Will swap direction
            "coauthor": EdgeType.AUTHORED,
            "same_movement": EdgeType.MEMBER_OF,
        }
        return mapping.get(rel_type, EdgeType.INFLUENCED_BY)
    
    def _compute_graph_metrics(
        self,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
    ) -> GraphData:
        """Compute graph metrics using NetworkX.
        
        Calculates:
            - Betweenness centrality for each node
            - Node degree
            - Top central nodes
        """
        if not nodes:
            return GraphData(nodes=[], edges=[])
        
        # Build NetworkX graph
        G = nx.Graph()
        
        for node in nodes:
            G.add_node(node.id, label=node.label)
        
        for edge in edges:
            G.add_edge(edge.source, edge.target)
        
        # Calculate metrics
        try:
            centrality = nx.betweenness_centrality(G)
        except Exception:
            centrality = {n.id: 0.0 for n in nodes}
        
        # Update nodes with metrics
        for node in nodes:
            node.centrality = centrality.get(node.id, 0.0)
            node.degree = G.degree(node.id) if node.id in G else 0
        
        # Find top central nodes
        sorted_by_centrality = sorted(
            nodes,
            key=lambda n: n.centrality or 0,
            reverse=True,
        )
        top_central = [n.id for n in sorted_by_centrality[:5]]
        
        return GraphData(
            nodes=nodes,
            edges=edges,
            central_nodes=top_central,
        )
    
    async def get_author_books(self, author_qid: str) -> list[dict]:
        """Get books written by an author (for graph expansion)."""
        query = f"""
        SELECT ?book ?bookLabel ?pubDate
        WHERE {{
            ?book wdt:P50 wd:{author_qid}.
            ?book wdt:P31/wdt:P279* wd:Q7725634.
            OPTIONAL {{ ?book wdt:P577 ?pubDate. }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 50
        """
        return await self.client.execute_query(query)
