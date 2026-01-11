import React, { useMemo, useState } from 'react';
import { Book } from '../types';
import { AuthorDetailModal } from './AuthorDetailModal';

interface AuthorWorksListProps {
    books: Book[];
}

export function AuthorWorksList({ books }: AuthorWorksListProps) {
    const [selectedAuthorQid, setSelectedAuthorQid] = useState<string | null>(null);

    // Track expanded authors for book list
    const [expandedAuthors, setExpandedAuthors] = useState<Record<string, boolean>>({});

    const toggleExpand = (author: string) => {
        setExpandedAuthors(prev => ({ ...prev, [author]: !prev[author] }));
    };

    // Group books by author
    const authorsMap = useMemo(() => {
        // Map stores Book[] keyed by "Author Name"
        // We also need to map "Author Name" -> "QID"
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
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 overflow-y-auto h-full pb-20">
                {sortedAuthors.map(author => (
                    <div key={author} className="card h-fit break-inside-avoid">
                        <div
                            className="text-left w-full group/btn cursor-pointer outline-none flex items-center justify-between"
                        >
                            <h3 className="card__title text-3xl font-bold text-accent mb-5 border-b border-white/10 pb-3 group-hover/btn:text-white transition-colors flex items-center gap-2">
                                {author}
                            </h3>
                            <button
                                className="ml-2 px-3 py-1 rounded-lg text-sm font-medium text-zinc-200 bg-zinc-800 border border-white/10 shadow hover:bg-accent hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"
                                onClick={() => toggleExpand(author)}
                                aria-expanded={!!expandedAuthors[author]}
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
                                            <h4 className="text-sm font-bold text-zinc-100 group-hover:text-accent transition-colors leading-tight">
                                                {book.title}
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
        </>
    );
}
