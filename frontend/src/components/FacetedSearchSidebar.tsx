/**
 * Faceted Search Sidebar Component
 * Provides filters for searching books by country, genre, and year range
 */

import { useCallback } from 'react';
import type { FilterState } from '../types';

// Common Wikidata QIDs for countries
export const COUNTRIES = [
    { qid: 'Q30', label: 'United States' },
    { qid: 'Q142', label: 'France' },
    { qid: 'Q145', label: 'United Kingdom' },
    { qid: 'Q183', label: 'Germany' },
    { qid: 'Q38', label: 'Italy' },
    { qid: 'Q159', label: 'Russia' },
    { qid: 'Q96', label: 'Mexico' },
    { qid: 'Q414', label: 'Argentina' },
    { qid: 'Q155', label: 'Brazil' },
    { qid: 'Q17', label: 'Japan' },
    { qid: 'Q148', label: 'China' },
    { qid: 'Q668', label: 'India' },
    { qid: 'Q218', label: 'Romania' },
];

// Common Wikidata QIDs for genres
export const GENRES = [
    { qid: 'Q8261', label: 'Novel' },
    { qid: 'Q49084', label: 'Short Story' },
    { qid: 'Q482', label: 'Poetry' },
    { qid: 'Q1422746', label: 'Magic Realism' },
    { qid: 'Q192782', label: 'Detective Fiction' },
    { qid: 'Q24925', label: 'Science Fiction' },
    { qid: 'Q1233720', label: 'Historical Novel' },
    { qid: 'Q131539', label: 'Tragedy' },
    { qid: 'Q40831', label: 'Comedy' },
    { qid: 'Q179461', label: 'Autobiography' },
];

interface FacetedSearchSidebarProps {
    filters: FilterState;
    onFiltersChange: (filters: FilterState) => void;
    onSearch: () => void;
    isLoading?: boolean;
    history?: FilterState[];
    onHistorySelect?: (filters: FilterState) => void;
}

export function FacetedSearchSidebar({
    filters,
    onFiltersChange,
    onSearch,
    isLoading = false,
    history = [],
    onHistorySelect,
}: FacetedSearchSidebarProps) {
    const updateFilter = useCallback(
        <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
            onFiltersChange({ ...filters, [key]: value });
        },
        [filters, onFiltersChange]
    );

    const handleReset = useCallback(() => {
        onFiltersChange({
            country: null,
            genre: null,
            yearStart: null,
            yearEnd: null,
            notableWorksOnly: false,
        });
    }, [onFiltersChange]);

    const formatFilter = (f: FilterState) => {
        const parts = [];
        if (f.country) {
            const c = COUNTRIES.find(c => c.qid === f.country);
            parts.push(c ? c.label : 'Unknown Country');
        }
        if (f.genre) {
            const g = GENRES.find(g => g.qid === f.genre);
            parts.push(g ? g.label : 'Unknown Genre');
        } else {
            parts.push('All Genres');
        }
        if (f.yearStart || f.yearEnd) {
            parts.push(`${f.yearStart || '?'}–${f.yearEnd || '?'}`);
        }
        if (f.notableWorksOnly) parts.push("🏆 Awards");

        if (parts.length === 0) return "All Books";
        return parts.join(', ');
    };

    const hasFilters = filters.country || filters.genre || filters.yearStart || filters.yearEnd || filters.notableWorksOnly;

    return (
        <aside className="sidebar">
            <div style={{ marginBottom: 'var(--spacing-6)' }}>
                <h2 style={{ fontSize: 'var(--font-size-xl)', marginBottom: 'var(--spacing-2)' }}>
                    Search Filters
                </h2>
                <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                    Explore Literature
                </p>
            </div>

            {/* Country Filter */}
            <div className="form-group">
                <label className="form-label" htmlFor="country">
                    Author Nationality
                </label>
                <select
                    id="country"
                    className="form-select"
                    value={filters.country || ''}
                    onChange={(e) => updateFilter('country', e.target.value || null)}
                >
                    <option value="">All Countries</option>
                    {COUNTRIES.map((c) => (
                        <option key={c.qid} value={c.qid}>
                            {c.label}
                        </option>
                    ))}
                </select>
            </div>

            {/* Genre Filter */}
            <div className="form-group">
                <label className="form-label" htmlFor="genre">
                    Genre
                </label>
                <select
                    id="genre"
                    className="form-select"
                    value={filters.genre || ''}
                    onChange={(e) => updateFilter('genre', e.target.value || null)}
                >
                    <option value="">All Genres</option>
                    {GENRES.map((g) => (
                        <option key={g.qid} value={g.qid}>
                            {g.label}
                        </option>
                    ))}
                </select>
            </div>

            {/* Year Range */}
            <div className="form-group">
                <label className="form-label">Publication Year Range</label>
                <div style={{ display: 'flex', gap: 'var(--spacing-2)', alignItems: 'center' }}>
                    <input
                        type="number"
                        className="form-input"
                        placeholder="From"
                        min={1000}
                        max={2030}
                        value={filters.yearStart || ''}
                        onChange={(e) => updateFilter('yearStart', e.target.value ? parseInt(e.target.value) : null)}
                        style={{ flex: 1 }}
                    />
                    <span style={{ color: 'var(--color-text-muted)' }}>–</span>
                    <input
                        type="number"
                        className="form-input"
                        placeholder="To"
                        min={1000}
                        max={2030}
                        value={filters.yearEnd || ''}
                        onChange={(e) => updateFilter('yearEnd', e.target.value ? parseInt(e.target.value) : null)}
                        style={{ flex: 1 }}
                    />
                </div>
            </div>

            {/* Notable Works Filter */}
            <div className="form-group">
                <label
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--spacing-2)',
                        cursor: 'pointer',
                        padding: 'var(--spacing-2)',
                        background: filters.notableWorksOnly ? 'var(--color-accent-muted)' : 'transparent',
                        border: `1px solid ${filters.notableWorksOnly ? 'var(--color-accent)' : 'var(--color-border)'}`,
                        borderRadius: 'var(--radius-sm)',
                        transition: 'all var(--transition-fast)',
                        fontSize: 'var(--font-size-sm)',
                    }}
                >
                    <input
                        type="checkbox"
                        checked={filters.notableWorksOnly}
                        onChange={(e) => updateFilter('notableWorksOnly', e.target.checked)}
                        style={{
                            width: 14,
                            height: 14,
                            accentColor: 'var(--color-accent)',
                            cursor: 'pointer',
                        }}
                    />
                    <span style={{ color: 'var(--color-text-primary)' }}>
                        🏆 Award Winners Only
                    </span>
                </label>
            </div>

            {/* Preset Quick Filters */}
            <div className="form-group">
                <label className="form-label">Quick Filters</label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--spacing-2)' }}>
                    <button
                        className="tag tag--accent"
                        style={{ cursor: 'pointer', border: 'none' }}
                        onClick={() => {
                            onFiltersChange({
                                country: 'Q30',
                                genre: null,
                                yearStart: 1920,
                                yearEnd: 1930,
                                notableWorksOnly: false,
                            });
                        }}
                    >
                        Lost Generation 🇺🇸
                    </button>
                    <button
                        className="tag tag--accent"
                        style={{ cursor: 'pointer', border: 'none' }}
                        onClick={() => {
                            onFiltersChange({
                                country: 'Q145', // United Kingdom
                                genre: null,
                                yearStart: 1837,
                                yearEnd: 1901,
                                notableWorksOnly: false,
                            });
                        }}
                    >
                        Victorian Era 🇬🇧
                    </button>


                </div>
            </div>

            {/* Search History */}
            {history.length > 0 && (
                <div className="form-group">
                    <label className="form-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        Recent Searches
                        <span style={{ fontSize: '0.7em', opacity: 0.6 }}>Last 5</span>
                    </label>
                    <select
                        className="form-select"
                        value=""
                        onChange={(e) => {
                            const idx = parseInt(e.target.value);
                            if (idx >= 0 && onHistorySelect) {
                                onHistorySelect(history[idx]);
                            }
                        }}
                        style={{ cursor: 'pointer' }}
                    >
                        <option value="" disabled>Select a previous search...</option>
                        {history.map((h, i) => (
                            <option key={i} value={i}>
                                {formatFilter(h)}
                            </option>
                        ))}
                    </select>
                </div>
            )}

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: 'var(--spacing-2)', marginTop: 'var(--spacing-6)' }}>
                <button
                    className="btn btn--primary"
                    onClick={onSearch}
                    disabled={isLoading}
                    style={{ flex: 1 }}
                >
                    {isLoading ? 'Searching...' : 'Search'}
                </button>
                {hasFilters && (
                    <button className="btn btn--secondary" onClick={handleReset}>
                        Reset
                    </button>
                )}
            </div>
        </aside>
    );
}
