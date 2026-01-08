# Literature Explorer Frontend

React-based interactive visualization platform for exploring literary networks.

## Overview

This frontend provides:
- **Force-directed graphs** for author influence networks (D3.js)
- **Interactive maps** showing author birthplaces and story settings (Leaflet)
- **Timeline visualization** of literary publications
- **Faceted search** with filters for country, genre, and time period

## Quick Start

### With Docker (Recommended)
```bash
# From project root
docker-compose up --build frontend
```

### Local Development
```bash
cd frontend
npm install
npm run dev
```

The app will be available at http://localhost:5173

## Architecture

```
src/
├── main.tsx             # React entry point
├── App.tsx              # Main application component
│
├── api/                 # Backend API integration
│   ├── client.ts        # Axios client with interceptors
│   └── hooks.ts         # TanStack Query hooks
│
├── components/          # React components
│   ├── ForceGraph.tsx           # D3.js author network graph
│   ├── BooksForceGraph.tsx      # Author-book relationship graph
│   ├── MapView.tsx              # React-Leaflet map
│   ├── Timeline.tsx             # Publication timeline
│   ├── FacetedSearchSidebar.tsx # Search filters
│   ├── AuthorDetailModal.tsx    # Author details popup
│   ├── AuthorWorksList.tsx      # Author's works list
│   └── EmptyState.tsx           # Loading/error states
│
├── types/               # TypeScript definitions
│   └── index.ts         # Shared interfaces
│
└── styles/
    └── index.css        # Global styles
```

## Components

### ForceGraph
D3.js force-directed graph for visualizing author influence networks.

**Features:**
- Nodes colored by type (author, movement)
- Node size based on betweenness centrality
- Interactive: drag nodes, zoom, pan
- Click nodes for author details
- Edge types shown with different styles

**Props:**
```typescript
interface ForceGraphProps {
    data: GraphData;          // Nodes and edges
    onNodeClick?: (node: GraphNode) => void;
    width?: number;
    height?: number;
}
```

### BooksForceGraph
Two-mode network showing author-book relationships.

**Features:**
- Authors and books as different node types
- Useful for exploring an author's bibliography
- Click to expand author's works

### MapView
React-Leaflet map with dual-layer visualization.

**Layers:**
- **Birthplaces** (Red pins): Where authors were born
- **Story Settings** (Blue pins): Where their stories take place

**Features:**
- Marker clustering for large datasets
- Popup on click with author/location details
- Layer toggle controls
- Zoom to fit all markers

**Props:**
```typescript
interface MapViewProps {
    birthplaces: GeoPoint[];
    settings: GeoPoint[];
    onPointClick?: (point: GeoPoint) => void;
}
```

### Timeline
Interactive timeline of literary publications.

**Features:**
- Horizontal scrollable timeline
- Filter by decade
- Click events to show book details
- Color-coded by genre

### FacetedSearchSidebar
Search filter panel for querying the backend.

**Filters:**
- **Country**: Author nationality (dropdown with common QIDs)
- **Genre**: Literary genre (dropdown)
- **Year Range**: Start and end year inputs
- **Presets**: Quick-select scenarios (Lost Generation, Magic Realism)

**Presets:**
| Preset | Filters Applied |
|--------|-----------------|
| Lost Generation | USA authors, 1920-1940 |
| Magic Realism | Genre: Q1422746, 1960-2000 |
| Victorian Literature | UK authors, 1837-1901 |

### AuthorDetailModal
Modal popup showing detailed author information.

**Displays:**
- Author name and image (if available)
- Birth/death dates and places
- Nationality and movements
- Notable works
- Influences (influenced by)
- Similar authors (recommendations)

### EmptyState
Unified component for loading, empty, and error states.

```typescript
// Loading state
<LoadingState message="Fetching authors..." />

// Empty state
<EmptyState 
    title="No results found"
    message="Try adjusting your filters"
/>

// Error state
<ErrorState 
    error={error}
    onRetry={() => refetch()}
/>
```

## API Integration

### Axios Client (`api/client.ts`)

Configured axios instance with:
- Base URL from Vite proxy (`/api`)
- 60-second timeout for Wikidata queries
- Error interceptors for 504/503 responses

```typescript
import { searchBooks, getAuthorNetwork, getLocations } from './api/client';

// Search books
const books = await searchBooks({
    country: 'Q30',
    genre: 'Q8261',
    year_start: 1920,
    year_end: 1950,
    limit: 50
});

// Get network graph
const graph = await getAuthorNetwork({
    authors: ['Q23434', 'Q188385'],
    depth: 2
});

// Get geographic data
const locations = await getLocations({
    layer: 'birthplaces',
    authors: ['Q23434']
});
```

### TanStack Query Hooks (`api/hooks.ts`)

React Query hooks with caching and automatic refetching:

```typescript
import { useSearchBooks, useAuthorNetwork, useLocations } from './api/hooks';

function MyComponent() {
    // Search with caching
    const { data: books, isLoading, error } = useSearchBooks({
        country: 'Q30',
        limit: 50
    }, { enabled: true });

    // Network graph
    const { data: graph } = useAuthorNetwork({
        authors: ['Q23434'],
        depth: 2
    }, { enabled: authors.length > 0 });

    // Geographic data
    const { data: locations } = useLocations({
        layer: 'birthplaces',
        authors: ['Q23434']
    });
}
```

**Query Key Structure:**
```typescript
queryKeys = {
    books: {
        all: ['books'],
        search: (params) => ['books', 'search', params],
        detail: (qid) => ['books', 'detail', qid],
    },
    graph: {
        network: (params) => ['graph', 'network', params],
    },
    geo: {
        locations: (params) => ['geo', 'locations', params],
    },
    recommendations: {
        similar: (qid, limit) => ['recommendations', 'similar', qid, limit],
    },
};
```

## TypeScript Types

All types mirror the backend Pydantic models:

```typescript
// Core entities
interface Book { qid, title, authors, author_qids, genre, publication_year, ... }
interface Author { qid, name, birth_place, movements, influenced_by, ... }
interface Location { qid, name, coordinates, country }

// Graph types
interface GraphNode { id, label, type, centrality, degree, metadata }
interface GraphEdge { source, target, type, weight }
interface GraphData { nodes, edges, node_count, edge_count, central_nodes }

// Geo types  
type GeoLayerType = 'birthplaces' | 'deathplaces' | 'publications' | 'settings';
interface GeoPoint { qid, name, latitude, longitude, layer, entity_qid, ... }
interface GeoResponse { layer, points, clusters, total_count, is_clustered }

// Search params
interface SearchParams { country?, genre?, year_start?, year_end?, limit?, offset? }
interface GraphParams { authors, depth?, include_coauthorship?, include_movements? }
interface GeoParams { layer, authors?, books?, cluster? }
```

## Styling

Global styles in `styles/index.css`:
- CSS custom properties for theming
- Responsive breakpoints
- Component-specific styles

**Color Scheme:**
- Primary: `#2563eb` (blue)
- Author nodes: `#ef4444` (red)
- Book nodes: `#22c55e` (green)
- Movement nodes: `#a855f7` (purple)
- Birthplace pins: `#ef4444` (red)
- Setting pins: `#3b82f6` (blue)

## Configuration

### Vite Config (`vite.config.ts`)

```typescript
export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
});
```

### Environment Variables

Create `.env.local` for local overrides:

```env
VITE_API_URL=http://localhost:8000
```

## Development

### Adding a New Component

1. Create component file in `src/components/`
2. Add TypeScript interface if needed in `src/types/index.ts`
3. Import and use in `App.tsx` or parent component

### Adding a New API Hook

1. Add function to `src/api/client.ts`
2. Create React Query hook in `src/api/hooks.ts`
3. Add query key to `queryKeys` object

### Building for Production

```bash
npm run build
```

Output will be in `dist/` directory.

## Dependencies

Key packages:
- `react` / `react-dom` - UI framework
- `@tanstack/react-query` - Data fetching & caching
- `axios` - HTTP client
- `d3` - Force graph visualization
- `react-leaflet` / `leaflet` - Map visualization
- `typescript` - Type safety
- `vite` - Build tool
