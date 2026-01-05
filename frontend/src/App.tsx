/**
 * Main App Component
 * Republic of Letters Data Exploration Platform
 */

import React, { useState, useCallback } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FacetedSearchSidebar } from './components/FacetedSearchSidebar';
import { ForceGraph } from './components/ForceGraph';
import { MapView } from './components/MapView';
import { Timeline } from './components/Timeline';
import { EmptyState, LoadingState, ErrorState } from './components/EmptyState';
import { useSearchBooks, useAuthorNetwork, useLocations } from './api/hooks';
import type { FilterState, ViewMode, Book, GraphNode, GeoLayerType } from './types';
import './styles/index.css';

// Create Query Client with defaults
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 2,
            staleTime: 5 * 60 * 1000,
            refetchOnWindowFocus: false,
        },
    },
});

type TabType = 'timeline' | 'graph' | 'map';

function AppContent() {
    // Filter state
    const [filters, setFilters] = useState<FilterState>({
        country: null,
        genre: null,
        yearStart: null,
        yearEnd: null,
    });

    // View state
    const [activeTab, setActiveTab] = useState<TabType>('timeline');
    const [searchTriggered, setSearchTriggered] = useState(false);
    const [selectedAuthors, setSelectedAuthors] = useState<string[]>([]);

    // Search query
    const {
        data: books = [],
        isLoading: booksLoading,
        error: booksError,
        refetch: refetchBooks,
    } = useSearchBooks(
        {
            country: filters.country || undefined,
            genre: filters.genre || undefined,
            year_start: filters.yearStart || undefined,
            year_end: filters.yearEnd || undefined,
            limit: 100,
        },
        { enabled: searchTriggered }
    );

    // Extract unique authors from books for graph
    const authorQids = React.useMemo(() => {
        const qids = new Set<string>();
        books.forEach((book) => {
            book.author_qids.forEach((qid) => qids.add(qid));
        });
        return Array.from(qids).slice(0, 10); // Limit for performance
    }, [books]);

    // Extract book QIDs for settings layer
    const bookQids = React.useMemo(() => {
        return books.map(b => b.qid).slice(0, 50); // Limit to top 50 books for performance
    }, [books]);

    // Graph query
    const {
        data: graphData,
        isLoading: graphLoading,
        error: graphError,
    } = useAuthorNetwork(
        { authors: authorQids, depth: 2 },
        { enabled: activeTab === 'graph' && authorQids.length > 0 }
    );

    // Geo query - Birthplaces
    const {
        data: birthplacesData,
        isLoading: birthplacesLoading,
        error: birthplacesError,
    } = useLocations(
        { layer: 'birthplaces' as GeoLayerType, authors: authorQids },
        { enabled: activeTab === 'map' && authorQids.length > 0 }
    );

    // Geo query - Settings (Narrative Locations)
    const {
        data: settingsData,
        isLoading: settingsLoading,
    } = useLocations(
        { layer: 'settings' as GeoLayerType, books: bookQids },
        { enabled: activeTab === 'map' && bookQids.length > 0 }
    );

    // Combine loading/error states
    const geoLoading = birthplacesLoading || settingsLoading;
    const geoError = birthplacesError;

    // Debug: log geo data when it changes
    React.useEffect(() => {
        if (birthplacesData) console.log('Birthplaces received:', birthplacesData);
        if (settingsData) console.log('Settings received:', settingsData);
        if (geoError) console.error('Geo error:', geoError);
    }, [birthplacesData, settingsData, geoError]);

    // Handlers
    const handleSearch = useCallback(() => {
        setSearchTriggered(true);
        refetchBooks();
    }, [refetchBooks]);

    const handleBookClick = useCallback((book: Book) => {
        console.log('Selected book:', book);
        // Could open a detail panel here
    }, []);

    const handleNodeClick = useCallback((node: GraphNode) => {
        console.log('Selected node:', node);
        if (node.type === 'author') {
            setSelectedAuthors((prev) =>
                prev.includes(node.id) ? prev.filter((id) => id !== node.id) : [...prev, node.id]
            );
        }
    }, []);

    // Determine current view content
    const renderContent = () => {
        if (!searchTriggered) {
            return (
                <EmptyState
                    icon="🔍"
                    title="Start Exploring"
                    description="Use the filters on the left to search for books and authors from the Literature Explorer."
                    action={{ label: 'Search All', onClick: handleSearch }}
                />
            );
        }

        if (booksLoading) {
            return <LoadingState message="Querying Wikidata..." />;
        }

        if (booksError) {
            return (
                <ErrorState
                    message={booksError.message || 'Failed to load books'}
                    onRetry={handleSearch}
                />
            );
        }

        if (books.length === 0) {
            return (
                <EmptyState
                    icon="📚"
                    title="No Books Found"
                    description="Try adjusting your filters or expanding the year range."
                />
            );
        }

        switch (activeTab) {
            case 'timeline':
                return <Timeline books={books} onBookClick={handleBookClick} />;

            case 'graph':
                if (graphLoading) {
                    return <LoadingState message="Building network..." />;
                }
                if (graphError) {
                    return <ErrorState message={graphError.message} />;
                }
                if (!graphData) {
                    return <EmptyState icon="🔗" title="Select authors to visualize their network" description="" />;
                }
                return (
                    <ForceGraph
                        data={graphData}
                        width={window.innerWidth - 360}
                        height={window.innerHeight - 140}
                        onNodeClick={handleNodeClick}
                    />
                );

            case 'map':
                if (geoLoading) {
                    return <LoadingState message="Loading locations..." />;
                }
                if (geoError) {
                    return <ErrorState message={geoError.message} />;
                }
                return (
                    <MapView
                        data={{
                            birthplaces: birthplacesData || { points: [], clusters: [], total_count: 0, is_clustered: false, layer: 'birthplaces' },
                            settings: settingsData || { points: [], clusters: [], total_count: 0, is_clustered: false, layer: 'settings' }
                        }}
                        height={window.innerHeight - 140}
                    />
                );

            default:
                return null;
        }
    };

    return (
        <div className="app">
            {/* Header */}
            <header className="header">
                <div className="header__logo">Literature Explorer</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-4)' }}>
                    {searchTriggered && books.length > 0 && (
                        <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                            {books.length} books found
                        </span>
                    )}
                </div>
            </header>

            {/* Sidebar */}
            <FacetedSearchSidebar
                filters={filters}
                onFiltersChange={setFilters}
                onSearch={handleSearch}
                isLoading={booksLoading}
            />

            {/* Main Content */}
            <main className="main">
                {/* Tabs */}
                <div className="tabs">
                    <button
                        className={`tab ${activeTab === 'timeline' ? 'tab--active' : ''}`}
                        onClick={() => setActiveTab('timeline')}
                    >
                        📅 Timeline
                    </button>
                    <button
                        className={`tab ${activeTab === 'graph' ? 'tab--active' : ''}`}
                        onClick={() => setActiveTab('graph')}
                    >
                        🔗 Network
                    </button>
                    <button
                        className={`tab ${activeTab === 'map' ? 'tab--active' : ''}`}
                        onClick={() => setActiveTab('map')}
                    >
                        🗺️ Map
                    </button>
                </div>

                {/* Content Area */}
                <div className="viz-container">{renderContent()}</div>
            </main>
        </div>
    );
}

export default function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <AppContent />
        </QueryClientProvider>
    );
}
