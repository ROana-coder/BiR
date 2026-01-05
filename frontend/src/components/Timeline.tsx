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

export function Timeline({ books, onBookClick }: TimelineProps) {
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

    return (
        <div style={{ padding: 'var(--spacing-6)', overflowX: 'auto' }}>
            <h3 style={{ marginBottom: 'var(--spacing-4)' }}>Publication Timeline</h3>

            <div
                style={{
                    display: 'flex',
                    gap: 'var(--spacing-2)',
                    alignItems: 'flex-end',
                    minHeight: 200,
                    paddingBottom: 'var(--spacing-8)',
                    position: 'relative',
                }}
            >
                {/* Timeline axis */}
                <div
                    style={{
                        position: 'absolute',
                        bottom: 0,
                        left: 0,
                        right: 0,
                        height: 2,
                        background: 'var(--color-border)',
                    }}
                />

                {timeline.map((entry) => {
                    const height = (entry.books.length / maxBooks) * 150 + 20;

                    return (
                        <div
                            key={entry.year}
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                minWidth: 60,
                            }}
                        >
                            {/* Bar */}
                            <div
                                style={{
                                    width: 40,
                                    height,
                                    background: `linear-gradient(180deg, var(--color-accent), var(--color-accent-muted))`,
                                    borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0',
                                    cursor: 'pointer',
                                    transition: 'transform var(--transition-fast)',
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    justifyContent: 'center',
                                    paddingTop: 'var(--spacing-1)',
                                }}
                                title={`${entry.books.length} books in ${entry.year}s`}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.transform = 'scaleY(1.05)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.transform = 'scaleY(1)';
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
                                    marginTop: 'var(--spacing-2)',
                                    fontSize: 'var(--font-size-xs)',
                                    color: 'var(--color-text-secondary)',
                                    transform: 'rotate(-45deg)',
                                    transformOrigin: 'top left',
                                    whiteSpace: 'nowrap',
                                }}
                            >
                                {entry.year}s
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Books list */}
            <div style={{ marginTop: 'var(--spacing-8)' }}>
                <h4 style={{ marginBottom: 'var(--spacing-4)', color: 'var(--color-text-secondary)' }}>
                    Recent Works
                </h4>
                <div
                    style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
                        gap: 'var(--spacing-4)',
                    }}
                >
                    {books.slice(0, 12).map((book) => (
                        <div
                            key={book.qid}
                            className="card"
                            style={{ cursor: 'pointer' }}
                            onClick={() => onBookClick?.(book)}
                        >
                            <div
                                style={{
                                    fontSize: 'var(--font-size-base)',
                                    fontWeight: 'var(--font-weight-medium)',
                                    marginBottom: 'var(--spacing-2)',
                                }}
                            >
                                {book.title}
                            </div>
                            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                                {book.authors.join(', ')}
                            </div>
                            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--spacing-1)' }}>
                                {book.publication_year || 'Unknown year'}
                                {book.genre && ` · ${book.genre}`}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
