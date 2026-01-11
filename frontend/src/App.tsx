/**
 * Main App Component
 * Literature Explorer Data Exploration Platform
 */

import React, { useState, useCallback } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FacetedSearchSidebar, COUNTRIES, GENRES } from './components/FacetedSearchSidebar';
import { ForceGraph } from './components/ForceGraph';
import { BooksForceGraph } from './components/BooksForceGraph';
import { AuthorWorksList } from './components/AuthorWorksList';
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
        notableWorksOnly: false,
    });

    // View state
    const [activeTab, setActiveTab] = useState<'timeline' | 'graph' | 'map' | 'works'>('graph');
    const [graphMode, setGraphMode] = useState<'influence' | 'works'>('influence');
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

    // Filter books based on notableWorksOnly
    const filteredBooks = React.useMemo(() => {
        if (!filters.notableWorksOnly) return books;
        return books.filter(book => book.awards && book.awards.length > 0);
    }, [books, filters.notableWorksOnly]);

    // Extract unique authors from filtered books for graph
    const authorQids = React.useMemo(() => {
        const qids = new Set<string>();
        filteredBooks.forEach((book) => {
            book.author_qids.forEach((qid) => qids.add(qid));
        });
        return Array.from(qids); // Limit removed per user request
    }, [filteredBooks]);

    // Create author QID to name mapping for ForceGraph
    const authorNames = React.useMemo(() => {
        const names = new Map<string, string>();
        filteredBooks.forEach((book) => {
            book.author_qids.forEach((qid, index) => {
                if (!names.has(qid) && book.authors[index]) {
                    names.set(qid, book.authors[index]);
                }
            });
        });
        return names;
    }, [filteredBooks]);

    // Extract book QIDs for settings layer
    const bookQids = React.useMemo(() => {
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
    React.useEffect(() => {
        if (birthplacesData) console.log('Birthplaces received:', birthplacesData);
        if (settingsData) console.log('Settings received:', settingsData);
        if (geoError) console.error('Geo error:', geoError);
    }, [birthplacesData, settingsData, geoError]);

    // History state
    const [filterHistory, setFilterHistory] = useState<FilterState[]>([]);

    // Handlers
    const handleSearch = useCallback(() => {
        setSearchTriggered(true);
        refetchBooks();

        // Update history
        setFilterHistory(prev => {
            // Avoid duplicates at the top of the stack
            if (prev.length > 0 && JSON.stringify(prev[0]) === JSON.stringify(filters)) {
                return prev;
            }
            const newHistory = [filters, ...prev];
            return newHistory.slice(0, 5); // Keep last 5
        });
    }, [refetchBooks, filters]);

    const handleRestoreFilter = useCallback((historyFilter: FilterState) => {
        setFilters(historyFilter);
        // Automatically trigger search? User might want to adjust first.
        // Let's just restore inputs. User can click Search.
    }, []);

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
                // Look up labels for QIDs
                const countryLabel = filters.country
                    ? COUNTRIES.find(c => c.qid === filters.country)?.label || filters.country
                    : null;
                const genreLabel = filters.genre
                    ? GENRES.find(g => g.qid === filters.genre)?.label || filters.genre
                    : null;

                return (
                    <Timeline
                        books={filteredBooks}
                        onBookClick={handleBookClick}
                        filterContext={{
                            country: countryLabel,
                            genre: genreLabel,
                            yearStart: filters.yearStart,
                            yearEnd: filters.yearEnd,
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
                const worksCountryLabel = filters.country
                    ? COUNTRIES.find(c => c.qid === filters.country)?.label || filters.country
                    : null;
                const worksGenreLabel = filters.genre
                    ? GENRES.find(g => g.qid === filters.genre)?.label || filters.genre
                    : null;

                return (
                    <AuthorWorksList
                        books={filteredBooks}
                        filterContext={{
                            country: worksCountryLabel,
                            genre: worksGenreLabel,
                            yearStart: filters.yearStart,
                            yearEnd: filters.yearEnd,
                            notableWorksOnly: filters.notableWorksOnly,
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
                    {searchTriggered && books.length > 0 && (
                        <div style={{ display: 'flex', gap: 'var(--spacing-4)', alignItems: 'center' }}>
                            <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                                {authorQids.length} authors found
                            </span>
                            <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                                {filteredBooks.length} books found
                                {filters.notableWorksOnly && filteredBooks.length !== books.length && (
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
                filters={filters}
                onFiltersChange={setFilters}
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
