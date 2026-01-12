import { useMemo, useState, useCallback } from 'react';
import { Book } from '../types';
import { AuthorDetailModal } from './AuthorDetailModal';
import { BookDetailModal } from './BookDetailModal';

interface FilterContext {
    country?: string | null;
    genre?: string | null;
    yearStart?: number | null;
    yearEnd?: number | null;
    notableWorksOnly?: boolean;
}

interface AuthorWorksListProps {
    books: Book[];
    filterContext?: FilterContext;
}

// Helper to escape CSV values
function escapeCSV(value: string): string {
    if (value.includes(',') || value.includes('"') || value.includes('\n')) {
        return `"${value.replace(/"/g, '""')}"`;
    }
    return value;
}

// Helper to convert books to CSV
function booksToCSV(books: Book[]): string {
    const headers = ['Title', 'Authors', 'Publication Year', 'Genres', 'Awards'];
    const rows = books.map(book => [
        escapeCSV(book.title),
        escapeCSV(book.authors.join('; ')),
        book.publication_year?.toString() || '',
        escapeCSV(book.genres.length > 0 ? book.genres.join('; ') : (book.genre || '')),
        escapeCSV(book.awards.join('; ')),
    ]);
    return [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
}

// Helper to convert books to XLS (TSV format that Excel can open)
function booksToXLS(books: Book[]): string {
    const headers = ['Title', 'Authors', 'Publication Year', 'Genres', 'Awards'];
    const rows = books.map(book => [
        book.title,
        book.authors.join('; '),
        book.publication_year?.toString() || '',
        book.genres.length > 0 ? book.genres.join('; ') : (book.genre || ''),
        book.awards.join('; '),
    ]);
    return [headers.join('\t'), ...rows.map(row => row.join('\t'))].join('\n');
}

// Helper to download a file
function downloadFile(content: string, filename: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Helper to generate descriptive filename
function generateFilename(filterContext?: FilterContext): string {
    const parts: string[] = [];

    // Use genre name as prefix if available, otherwise "books"
    if (filterContext?.genre) {
        parts.push(filterContext.genre.toLowerCase().replace(/\s+/g, '_'));
    } else {
        parts.push('books');
    }

    if (filterContext?.country) {
        // Clean up country name for filename
        parts.push(filterContext.country.toLowerCase().replace(/\s+/g, '_'));
    }
    if (filterContext?.yearStart || filterContext?.yearEnd) {
        const start = filterContext.yearStart || '';
        const end = filterContext.yearEnd || '';
        if (start && end) {
            parts.push(`${start}-${end}`);
        } else if (start) {
            parts.push(`from_${start}`);
        } else if (end) {
            parts.push(`until_${end}`);
        }
    }
    if (filterContext?.notableWorksOnly) {
        parts.push('awards');
    }

    const now = new Date();
    const timestamp = `${now.toISOString().split('T')[0]}_${now.toTimeString().slice(0, 8).replace(/:/g, '-')}`;
    parts.push(timestamp);

    return parts.join('_');
}

export function AuthorWorksList({ books, filterContext }: AuthorWorksListProps) {
    const [selectedAuthorQid, setSelectedAuthorQid] = useState<string | null>(null);
    const [selectedBook, setSelectedBook] = useState<Book | null>(null);

    // Track expanded authors for book list
    const [expandedAuthors, setExpandedAuthors] = useState<Record<string, boolean>>({});

    const toggleExpand = (author: string) => {
        setExpandedAuthors(prev => ({ ...prev, [author]: !prev[author] }));
    };

    // Export handlers
    const handleExportCSV = useCallback(() => {
        const csv = booksToCSV(books);
        const filename = generateFilename(filterContext);
        downloadFile(csv, `${filename}.csv`, 'text/csv;charset=utf-8;');
    }, [books, filterContext]);

    const handleExportXLS = useCallback(() => {
        const xls = booksToXLS(books);
        const filename = generateFilename(filterContext);
        downloadFile(xls, `${filename}.xls`, 'application/vnd.ms-excel;charset=utf-8;');
    }, [books, filterContext]);

    // Group books by author
    const authorsMap = useMemo(() => {
        // Map stores Book[] keyed by "Author Name"
        // I also need to map "Author Name" -> "QID"
        const map = new Map<string, Book[]>();
        const qidMap = new Map<string, string>();

        books.forEach(book => {
            if (book.authors.length === 0) {
                // Handle unknown authors
                const unknown = 'Unknown Author';
                if (!map.has(unknown)) map.set(unknown, []);
                map.get(unknown)?.push(book);
            } else {
                book.authors.forEach((author, idx) => {
                    if (!map.has(author)) map.set(author, []);
                    map.get(author)?.push(book);

                    // Capture QID if available and not yet set
                    if (!qidMap.has(author) && book.author_qids[idx]) {
                        qidMap.set(author, book.author_qids[idx]);
                    }
                });
            }
        });

        return { map, qidMap };
    }, [books]);

    // Sort authors alphabetically
    const sortedAuthors = useMemo(() => {
        return Array.from(authorsMap.map.keys()).sort();
    }, [authorsMap]);

    const handleAuthorClick = (author: string) => {
        const qid = authorsMap.qidMap.get(author);
        if (qid) {
            setSelectedAuthorQid(qid);
        }
    };

    if (books.length === 0) {
        return (
            <div className="empty-state">
                <div className="empty-state__icon">📚</div>
                <h3 className="empty-state__title">No Works Found</h3>
                <p className="empty-state__description">
                    Adjust your search filters to explore the library.
                </p>
            </div>
        );
    }

    return (
        <>
            {/* Export Header */}
            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: 'var(--spacing-4) var(--spacing-6)',
                    borderBottom: '1px solid var(--color-border)',
                    background: 'var(--color-bg-elevated)',
                }}
            >
                <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                    {books.length} works from {sortedAuthors.length} authors
                </span>
                <div style={{ display: 'flex', gap: 'var(--spacing-2)' }}>
                    <button
                        onClick={handleExportCSV}
                        className="btn btn--secondary"
                        style={{ fontSize: 'var(--font-size-xs)', padding: 'var(--spacing-2) var(--spacing-3)' }}
                    >
                        📥 Export CSV
                    </button>
                    <button
                        onClick={handleExportXLS}
                        className="btn btn--secondary"
                        style={{ fontSize: 'var(--font-size-xs)', padding: 'var(--spacing-2) var(--spacing-3)' }}
                    >
                        📊 Export XLS
                    </button>
                </div>
            </div>

            <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 overflow-y-auto h-full pb-20">
                {sortedAuthors.map(author => (
                    <div key={author} className="card h-fit break-inside-avoid">
                        <div
                            className="text-left w-full group/btn cursor-pointer outline-none flex items-center justify-between"
                        >
                            <h3
                                onClick={() => handleAuthorClick(author)}
                                style={{
                                    fontSize: 'var(--font-size-lg)',
                                    fontWeight: 'var(--font-weight-bold)',
                                    color: 'var(--color-text-primary)',
                                    marginBottom: 'var(--spacing-3)',
                                    borderBottom: '1px solid var(--color-border)',
                                    paddingBottom: 'var(--spacing-3)',
                                    cursor: 'pointer',
                                    transition: 'color var(--transition-fast)',
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.color = 'var(--color-accent)';
                                    e.currentTarget.style.textDecoration = 'underline';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.color = 'var(--color-text-primary)';
                                    e.currentTarget.style.textDecoration = 'none';
                                }}
                                title="Click to view author details"
                            >
                                {author} <svg style={{ width: '0.9em', height: '0.9em', marginLeft: '0.25em', display: 'inline-block', verticalAlign: 'middle', opacity: 0.4 }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" /></svg>
                            </h3>
                            <button
                                onClick={() => toggleExpand(author)}
                                aria-expanded={!!expandedAuthors[author]}
                                style={{
                                    padding: 'var(--spacing-2) var(--spacing-3)',
                                    fontSize: 'var(--font-size-xs)',
                                    fontWeight: 'var(--font-weight-medium)',
                                    color: 'var(--color-text-primary)',
                                    background: 'var(--color-bg)',
                                    border: '1px solid var(--color-border)',
                                    borderRadius: 'var(--radius-sm)',
                                    cursor: 'pointer',
                                    transition: 'all var(--transition-fast)',
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.background = 'var(--color-accent)';
                                    e.currentTarget.style.borderColor = 'var(--color-accent)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.background = 'var(--color-bg)';
                                    e.currentTarget.style.borderColor = 'var(--color-border)';
                                }}
                            >
                                {expandedAuthors[author] ? 'Hide Books' : 'Show Books'}
                            </button>
                        </div>
                        {expandedAuthors[author] && (
                            <div className="space-y-3">
                                {authorsMap.map.get(author)?.map((book) => (
                                    <div
                                        key={book.qid}
                                        style={{
                                            backgroundColor: '#27272a', // zinc-800
                                            border: '1px solid #3f3f46', // zinc-700
                                            borderRadius: '8px',
                                            padding: '12px',
                                            marginBottom: '10px'
                                        }}
                                        className="group hover:bg-zinc-700 transition-colors"
                                    >
                                        <div className="flex justify-between items-start gap-3">
                                            <h4
                                                onClick={() => setSelectedBook(book)}
                                                style={{
                                                    fontSize: '0.875rem',
                                                    fontWeight: 'bold',
                                                    color: '#f4f4f5',
                                                    cursor: 'pointer',
                                                    transition: 'color 0.15s, text-decoration 0.15s',
                                                }}
                                                onMouseEnter={(e) => {
                                                    e.currentTarget.style.color = 'var(--color-accent)';
                                                    e.currentTarget.style.textDecoration = 'underline';
                                                }}
                                                onMouseLeave={(e) => {
                                                    e.currentTarget.style.color = '#f4f4f5';
                                                    e.currentTarget.style.textDecoration = 'none';
                                                }}
                                                title="Click to view book details"
                                            >
                                                {book.title} <svg style={{ width: '0.9em', height: '0.9em', marginLeft: '0.25em', display: 'inline-block', verticalAlign: 'middle', opacity: 0.4 }} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" /></svg>
                                            </h4>
                                            <span className="text-xs text-zinc-500 font-mono whitespace-nowrap pt-0.5 bg-black/20 px-1.5 py-0.5 rounded">
                                                {book.publication_year || '-'}
                                            </span>
                                        </div>
                                        {/* Awards / Meta */}
                                        <div className="flex flex-wrap gap-2 mt-2">
                                            {book.awards.length > 0 && (
                                                book.awards.map((award, idx) => (
                                                    <span
                                                        key={idx}
                                                        className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                                                    >
                                                        🏆 {award}
                                                    </span>
                                                ))
                                            )}
                                            {/* Default badge if 'Novel' etc. */}
                                            {book.genre && (
                                                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">
                                                    {book.genre}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {selectedAuthorQid && (
                <AuthorDetailModal
                    qid={selectedAuthorQid}
                    onClose={() => setSelectedAuthorQid(null)}
                />
            )}

            {selectedBook && (
                <BookDetailModal
                    book={selectedBook}
                    onClose={() => setSelectedBook(null)}
                />
            )}
        </>
    );
}
