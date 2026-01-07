/**
 * Timeline Visualization Component
 * Shows chronological spread of books and authors
 */

import React, { useMemo } from 'react';
import type { Book } from '../types';

interface TimelineProps {
    books: Book[];
    onBookClick?: (book: Book) => void;
}

interface TimelineEntry {
    year: number;
    books: Book[];
}

export function Timeline({ books }: TimelineProps) {
    // Group books by decade
    const timeline = useMemo(() => {
        const grouped = new Map<number, Book[]>();

        books.forEach((book) => {
            if (book.publication_year) {
                const decade = Math.floor(book.publication_year / 10) * 10;
                if (!grouped.has(decade)) {
                    grouped.set(decade, []);
                }
                grouped.get(decade)!.push(book);
            }
        });

        return Array.from(grouped.entries())
            .map(([decade, books]) => ({ year: decade, books }))
            .sort((a, b) => a.year - b.year);
    }, [books]);

    if (!books.length) {
        return (
            <div className="empty-state">
                <div className="empty-state__icon">📅</div>
                <h3 className="empty-state__title">No Timeline Data</h3>
                <p className="empty-state__description">
                    Search for books to see their chronological distribution.
                </p>
            </div>
        );
    }

    const maxBooks = Math.max(...timeline.map((t) => t.books.length));
    const minYear = timeline.length > 0 ? timeline[0].year : 0;
    const maxYear = timeline.length > 0 ? timeline[timeline.length - 1].year + 9 : 0;
    const peakDecade = timeline.reduce((max, curr) => (curr.books.length > max.books.length ? curr : max), timeline[0] || { year: 0, books: [] });

    return (
        <div style={{ padding: 'var(--spacing-6)', overflowX: 'auto' }}>
            <h3 style={{ marginBottom: 'var(--spacing-6)' }}>Timeline Analysis</h3>

            {/* Stats Summary */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: 'var(--spacing-4)',
                marginBottom: 'var(--spacing-8)',
                padding: 'var(--spacing-4)',
                background: 'var(--color-bg-elevated)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--color-border)'
            }}>
                <div>
                    <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Total Works</div>
                    <div style={{ fontSize: 'var(--font-size-3xl)', fontWeight: 'bold', color: 'var(--color-text-primary)' }}>{books.length}</div>
                </div>
                <div>
                    <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Time Span</div>
                    <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'bold', color: 'var(--color-text-primary)' }}>
                        {minYear} - {maxYear}
                    </div>
                </div>
                <div>
                    <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Peak Decade</div>
                    <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'bold', color: 'var(--color-accent)' }}>
                        {peakDecade.year}s <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'normal' }}>({peakDecade.books.length} books)</span>
                    </div>
                </div>
            </div>

            <h4 style={{ marginBottom: 'var(--spacing-4)', color: 'var(--color-text-secondary)' }}>Distribution by Decade</h4>

            <div
                style={{
                    display: 'flex',
                    gap: 'var(--spacing-2)',
                    alignItems: 'flex-end',
                    minHeight: 300,
                    paddingBottom: 'var(--spacing-8)',
                    position: 'relative',
                    background: 'linear-gradient(to bottom, transparent, var(--color-bg-elevated))',
                    borderRadius: 'var(--radius-lg)',
                    padding: 'var(--spacing-6)'
                }}
            >
                {/* Timeline axis */}
                <div
                    style={{
                        position: 'absolute',
                        bottom: 'var(--spacing-6)',
                        left: 'var(--spacing-6)',
                        right: 'var(--spacing-6)',
                        height: 2,
                        background: 'var(--color-border)',
                    }}
                />

                {timeline.map((entry) => {
                    const height = (entry.books.length / maxBooks) * 200 + 20;

                    return (
                        <div
                            key={entry.year}
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                minWidth: 60,
                                flex: 1,
                            }}
                        >
                            {/* Bar */}
                            <div
                                style={{
                                    width: '60%',
                                    maxWidth: 50,
                                    height,
                                    background: `linear-gradient(180deg, var(--color-accent), var(--color-accent-muted))`,
                                    borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0',
                                    cursor: 'pointer',
                                    transition: 'all var(--transition-fast)',
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    justifyContent: 'center',
                                    paddingTop: 'var(--spacing-1)',
                                    position: 'relative',
                                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
                                }}
                                title={`${entry.books.length} books in ${entry.year}s`}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.transform = 'scaleY(1.05)';
                                    e.currentTarget.style.filter = 'brightness(1.1)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.transform = 'scaleY(1)';
                                    e.currentTarget.style.filter = 'brightness(1)';
                                }}
                            >
                                <span
                                    style={{
                                        fontSize: 'var(--font-size-xs)',
                                        fontWeight: 'var(--font-weight-bold)',
                                        color: 'var(--color-bg)',
                                    }}
                                >
                                    {entry.books.length}
                                </span>
                            </div>

                            {/* Year label */}
                            <div
                                style={{
                                    marginTop: 'var(--spacing-4)',
                                    fontSize: 'var(--font-size-xs)',
                                    color: 'var(--color-text-secondary)',
                                    fontWeight: '500'
                                }}
                            >
                                {entry.year}s
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
