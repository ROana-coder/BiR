/**
 * Main App Component
 * Literature Explorer Data Exploration Platform
 */

import { useState, useMemo, useCallback, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FacetedSearchSidebar, COUNTRIES, GENRES } from './components/FacetedSearchSidebar';
import { ForceGraph } from './components/ForceGraph';
import { BooksForceGraph } from './components/BooksForceGraph';
import { AuthorWorksList } from './components/AuthorWorksList';
import { MapView } from './components/MapView';
import { Timeline } from './components/Timeline';
import { EmptyState, LoadingState, ErrorState } from './components/EmptyState';
import { useSearchBooks, useAuthorNetwork, useLocations } from './api/hooks';
import type { FilterState, Book, GraphNode, GeoLayerType } from './types';
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



function AppContent() {
    // UI Filter state (what the user is editing)
    const [uiFilters, setUiFilters] = useState<FilterState>({
        country: null,
        genre: null,
        yearStart: null,
        yearEnd: null,
        notableWorksOnly: false,
    });

    // Active Search State (what is currently queried)
    const [activeFilters, setActiveFilters] = useState<FilterState | null>(null);

    // View state
    const [activeTab, setActiveTab] = useState<'timeline' | 'graph' | 'map' | 'works'>('graph');
    const [graphMode, setGraphMode] = useState<'influence' | 'works'>('influence');


    // Search query
    const {
        data: books = [],
        isLoading: booksLoading,
        error: booksError,
    } = useSearchBooks(
        {
            country: activeFilters?.country || undefined,
            genre: activeFilters?.genre || undefined,
            year_start: activeFilters?.yearStart || undefined,
            year_end: activeFilters?.yearEnd || undefined,
            limit: 100,
        },
        { enabled: activeFilters !== null }
    );

    // Filter books based on notableWorksOnly
    const filteredBooks = useMemo(() => {
        // Safety check: ensure books is an array
        if (!Array.isArray(books)) return [];
        if (!activeFilters?.notableWorksOnly) return books;
        return books.filter(book => book.awards && book.awards.length > 0);
    }, [books, activeFilters?.notableWorksOnly]);

    // Extract unique authors from filtered books for graph
    const authorQids = useMemo(() => {
        const qids = new Set<string>();
        if (Array.isArray(filteredBooks)) {
            filteredBooks.forEach((book) => {
                if (Array.isArray(book.author_qids)) {
                    book.author_qids.forEach((qid) => qids.add(qid));
                }
            });
        }
        return Array.from(qids);
    }, [filteredBooks]);

    // Create author QID to name mapping for ForceGraph
    const authorNames = useMemo(() => {
        const names = new Map<string, string>();
        if (Array.isArray(filteredBooks)) {
            filteredBooks.forEach((book) => {
                if (Array.isArray(book.author_qids) && Array.isArray(book.authors)) {
                    book.author_qids.forEach((qid, index) => {
                        if (!names.has(qid) && book.authors[index]) {
                            names.set(qid, book.authors[index]);
                        }
                    });
                }
            });
        }
        return names;
    }, [filteredBooks]);

    // Extract book QIDs for settings layer
    const bookQids = useMemo(() => {
        if (!Array.isArray(filteredBooks)) return [];
        return filteredBooks.map(b => b.qid).slice(0, 50); // Limit to top 50 books for performance
    }, [filteredBooks]);

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
    useEffect(() => {
        if (birthplacesData) console.log('Birthplaces received:', birthplacesData);
        if (settingsData) console.log('Settings received:', settingsData);
        if (geoError) console.error('Geo error:', geoError);
    }, [birthplacesData, settingsData, geoError]);

    // History state
    const [filterHistory, setFilterHistory] = useState<FilterState[]>([]);

    // Handlers
    const handleSearch = useCallback(() => {
        // Apply current UI filters as active filters
        setActiveFilters(uiFilters);
        // Refetch is handled automatically by react-query when activeFilters changes

        // Update history
        setFilterHistory(prev => {
            // Remove any existing duplicate of the current filter
            const filtered = prev.filter(f => JSON.stringify(f) !== JSON.stringify(uiFilters));
            // Add current filter to the top
            const newHistory = [uiFilters, ...filtered];
            return newHistory.slice(0, 5); // Keep last 5
        });
    }, [uiFilters]);

    const handleRestoreFilter = useCallback((historyFilter: FilterState) => {
        setUiFilters(historyFilter);
        setActiveFilters(historyFilter);
    }, []);

    const handleBookClick = useCallback((book: Book) => {
        console.log('Selected book:', book);
        // Could open a detail panel here
    }, []);

    const handleNodeClick = useCallback((node: GraphNode) => {
        console.log('Selected node:', node);
        if (node.type === 'author') {
            console.log('Selected author:', node.id);
        }
    }, []);

    // Determine current view content
    const renderContent = () => {
        if (!activeFilters) {
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
                // Look up labels for QIDs
                const countryLabel = activeFilters.country
                    ? COUNTRIES.find(c => c.qid === activeFilters.country)?.label || activeFilters.country
                    : null;
                const genreLabel = activeFilters.genre
                    ? GENRES.find(g => g.qid === activeFilters.genre)?.label || activeFilters.genre
                    : null;

                return (
                    <Timeline
                        books={filteredBooks}
                        onBookClick={handleBookClick}
                        filterContext={{
                            country: countryLabel,
                            genre: genreLabel,
                            yearStart: activeFilters.yearStart,
                            yearEnd: activeFilters.yearEnd,
                        }}
                    />
                );

            case 'graph':
                if (graphLoading && graphMode === 'influence') return <LoadingState message="Building citation network..." />;
                if (graphError && graphMode === 'influence') return <ErrorState message="Failed to load network graph." />;

                return (
                    <div className="flex flex-col h-full relative">
                        {/* Graph Mode Toggle */}
                        <div className="absolute top-4 left-4 z-10 flex gap-1 bg-zinc-900/90 p-1 rounded-md border border-white/10 backdrop-blur-sm">
                            <button
                                onClick={() => setGraphMode('influence')}
                                className={`tab ${graphMode === 'influence' ? 'tab--active' : ''}`}
                            >
                                Author Influence
                            </button>
                            <button
                                onClick={() => setGraphMode('works')}
                                className={`tab ${graphMode === 'works' ? 'tab--active' : ''}`}
                            >
                                Filtered Works
                            </button>
                        </div>

                        <div className="flex-1 min-h-0 bg-zinc-950 rounded-lg border border-white/5 overflow-hidden">
                            {graphMode === 'influence' ? (
                                <ForceGraph
                                    data={graphData || { nodes: [], edges: [], node_count: 0, edge_count: 0, central_nodes: [] }}
                                    width={1200}
                                    height={800}
                                    onNodeClick={handleNodeClick}
                                    highlightedNodeIds={authorQids}
                                    authorNames={authorNames}
                                />
                            ) : (
                                <BooksForceGraph
                                    books={filteredBooks}
                                    width={1200}
                                    height={800}
                                    onNodeClick={(node) => console.log(node)}
                                />
                            )}
                        </div>
                    </div>
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

            case 'works':
                // Look up labels for QIDs for export filename
                const worksCountryLabel = activeFilters.country
                    ? COUNTRIES.find(c => c.qid === activeFilters.country)?.label || activeFilters.country
                    : null;
                const worksGenreLabel = activeFilters.genre
                    ? GENRES.find(g => g.qid === activeFilters.genre)?.label || activeFilters.genre
                    : null;

                return (
                    <AuthorWorksList
                        books={filteredBooks}
                        filterContext={{
                            country: worksCountryLabel,
                            genre: worksGenreLabel,
                            yearStart: activeFilters.yearStart,
                            yearEnd: activeFilters.yearEnd,
                            notableWorksOnly: activeFilters.notableWorksOnly,
                        }}
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
                    {activeFilters && books.length > 0 && (
                        <div style={{ display: 'flex', gap: 'var(--spacing-4)', alignItems: 'center' }}>
                            <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                                {authorQids.length} authors found
                            </span>
                            <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                                {filteredBooks.length} books found
                                {activeFilters?.notableWorksOnly && filteredBooks.length !== books.length && (
                                    <span style={{ color: 'var(--color-accent)', marginLeft: 4 }}>
                                        (🏆 {books.length - filteredBooks.length} filtered)
                                    </span>
                                )}
                            </span>
                        </div>
                    )}
                </div>
            </header>

            {/* Sidebar */}
            <FacetedSearchSidebar
                filters={uiFilters}
                onFiltersChange={setUiFilters}
                onSearch={handleSearch}
                isLoading={booksLoading}
                history={filterHistory}
                onHistorySelect={handleRestoreFilter}
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
                    <button
                        className={`tab ${activeTab === 'works' ? 'tab--active' : ''}`}
                        onClick={() => setActiveTab('works')}
                    >
                        📜 Works
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
