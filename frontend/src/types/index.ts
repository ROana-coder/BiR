/**
 * TypeScript interfaces for Republic of Letters API
 * Mirrors backend Pydantic models
 */

// === Core Entities ===

export interface Location {
    qid: string;
    name: string;
    coordinates: [number, number] | null;
    country: string | null;
}

export interface Author {
    qid: string;
    name: string;
    birth_date: string | null;
    death_date: string | null;
    birth_place: Location | null;
    death_place: Location | null;
    nationality: string | null;
    nationality_qid: string | null;
    movements: string[];
    movement_qids: string[];
    notable_works: string[];
    notable_work_qids: string[];
    influenced_by: string[];
    influenced_by_qids: string[];
    occupations: string[];
}

export interface Book {
    qid: string;
    title: string;
    publication_date: string | null;
    publication_year: number | null;
    authors: string[];
    author_qids: string[];
    genre: string | null;
    genre_qid: string | null;
    genres: string[];
    genre_qids: string[];
    publication_place: Location | null;
    narrative_locations: Location[];
    language: string | null;
    language_qid: string | null;
}

// === Graph Types ===

export type NodeType = 'author' | 'book' | 'movement' | 'location';
export type EdgeType = 'authored' | 'influenced_by' | 'student_of' | 'member_of';

export interface GraphNode {
    id: string;
    label: string;
    type: NodeType;
    metadata: Record<string, unknown>;
    centrality: number | null;
    degree: number | null;
}

export interface GraphEdge {
    source: string;
    target: string;
    type: EdgeType;
    weight: number;
    label: string | null;
}

export interface GraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
    node_count: number;
    edge_count: number;
    central_nodes: string[];
}

// === Geo Types ===

export type GeoLayerType = 'birthplaces' | 'deathplaces' | 'publications' | 'settings';

export interface GeoPoint {
    qid: string;
    name: string;
    latitude: number;
    longitude: number;
    layer: GeoLayerType;
    entity_qid: string | null;
    entity_name: string | null;
    entity_type: string | null;
    year: number | null;
}

export interface GeoCluster {
    center_latitude: number;
    center_longitude: number;
    point_count: number;
    layer: GeoLayerType;
    sample_points: GeoPoint[];
    bounds: [number, number, number, number] | null;
}

export interface GeoResponse {
    points: GeoPoint[];
    clusters: GeoCluster[];
    total_count: number;
    is_clustered: boolean;
    layer: GeoLayerType;
}

// === Recommendation Types ===

export interface SimilarAuthor {
    qid: string;
    name: string;
    similarity: number;
    shared_movements: string[];
    shared_genres: string[];
}

// === API Request Types ===

export interface SearchParams {
    country?: string;
    genre?: string;
    location?: string;
    year_start?: number;
    year_end?: number;
    limit?: number;
    offset?: number;
}

export interface GraphParams {
    authors: string[];
    depth?: number;
    include_coauthorship?: boolean;
    include_movements?: boolean;
}

export interface GeoParams {
    layer: GeoLayerType;
    authors?: string[];
    books?: string[];
    cluster?: boolean;
}

// === UI State Types ===

export interface FilterState {
    country: string | null;
    genre: string | null;
    yearStart: number | null;
    yearEnd: number | null;
}

export type ViewMode = 'search' | 'graph' | 'map' | 'timeline';

export interface AppState {
    viewMode: ViewMode;
    filters: FilterState;
    selectedAuthors: string[];
    selectedBooks: string[];
}
