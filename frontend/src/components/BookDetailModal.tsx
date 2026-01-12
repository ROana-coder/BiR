import { createPortal } from 'react-dom';
import { Book } from '../types';

interface BookDetailModalProps {
    book: Book;
    onClose: () => void;
}

export function BookDetailModal({ book, onClose }: BookDetailModalProps) {
    return createPortal(
        <div
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                zIndex: 9999,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'rgba(0, 0, 0, 0.8)'
            }}
            onClick={onClose}
        >
            <div
                style={{
                    width: '100%',
                    maxWidth: '36rem',
                    maxHeight: '80vh',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column',
                    backgroundColor: '#18181b',
                    borderRadius: '12px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                    position: 'relative'
                }}
                onClick={e => e.stopPropagation()}
            >

                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute',
                        top: '1rem',
                        right: '1rem',
                        zIndex: 50,
                        padding: '0.5rem',
                        borderRadius: '9999px',
                        backgroundColor: 'rgba(0, 0, 0, 0.5)',
                        border: 'none',
                        cursor: 'pointer',
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'background-color 0.2s'
                    }}
                    onMouseEnter={e => e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.7)'}
                    onMouseLeave={e => e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.5)'}
                    aria-label="Close"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" style={{ display: 'block' }}>
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                </button>

                <div style={{ padding: '2rem', overflowY: 'auto' }}>
                    <div style={{ marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'white', marginBottom: '0.5rem' }}>
                            📖 {book.title}
                        </h2>
                        <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.875rem', color: '#a1a1aa' }}>
                            {book.publication_year && <span>Published: {book.publication_year}</span>}
                            {book.genre && <span>• {book.genre}</span>}
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        {book.authors.length > 0 && (
                            <div>
                                <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#71717a', marginBottom: '0.5rem' }}>
                                    ✍️ Authors
                                </h4>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    {book.authors.map((author, idx) => (
                                        <span
                                            key={idx}
                                            style={{
                                                padding: '0.25rem 0.75rem',
                                                backgroundColor: '#27272a',
                                                borderRadius: '9999px',
                                                fontSize: '0.875rem',
                                                color: '#e4e4e7'
                                            }}
                                        >
                                            {author}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}


                        {book.publisher && (
                            <div>
                                <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#71717a', marginBottom: '0.5rem' }}>
                                    🏢 Publisher
                                </h4>
                                <span style={{ color: '#e4e4e7' }}>{book.publisher}</span>
                            </div>
                        )}


                        {book.publication_place && (
                            <div>
                                <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#71717a', marginBottom: '0.5rem' }}>
                                    📍 Place of Publication
                                </h4>
                                <span style={{ color: '#e4e4e7' }}>
                                    {book.publication_place.name}
                                    {book.publication_place.country && `, ${book.publication_place.country}`}
                                </span>
                            </div>
                        )}


                        {(book.languages?.length > 0 || book.language) && (
                            <div>
                                <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#71717a', marginBottom: '0.5rem' }}>
                                    🌍 Languages / Translations
                                </h4>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    {book.languages?.length > 0 ? (
                                        book.languages.map((lang, idx) => (
                                            <span
                                                key={idx}
                                                style={{
                                                    padding: '0.25rem 0.75rem',
                                                    backgroundColor: '#1e3a5f',
                                                    border: '1px solid #3b82f6',
                                                    borderRadius: '9999px',
                                                    fontSize: '0.75rem',
                                                    color: '#93c5fd'
                                                }}
                                            >
                                                {lang}
                                            </span>
                                        ))
                                    ) : book.language ? (
                                        <span
                                            style={{
                                                padding: '0.25rem 0.75rem',
                                                backgroundColor: '#1e3a5f',
                                                border: '1px solid #3b82f6',
                                                borderRadius: '9999px',
                                                fontSize: '0.75rem',
                                                color: '#93c5fd'
                                            }}
                                        >
                                            {book.language}
                                        </span>
                                    ) : null}
                                </div>
                            </div>
                        )}


                        {book.awards.length > 0 && (
                            <div>
                                <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#71717a', marginBottom: '0.5rem' }}>
                                    🏆 Awards
                                </h4>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    {book.awards.map((award, idx) => (
                                        <span
                                            key={idx}
                                            style={{
                                                padding: '0.25rem 0.75rem',
                                                backgroundColor: 'rgba(234, 179, 8, 0.1)',
                                                border: '1px solid rgba(234, 179, 8, 0.3)',
                                                borderRadius: '9999px',
                                                fontSize: '0.75rem',
                                                color: '#fbbf24'
                                            }}
                                        >
                                            {award}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}


                        {book.genres?.length > 0 && (
                            <div>
                                <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#71717a', marginBottom: '0.5rem' }}>
                                    📚 Genres
                                </h4>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    {book.genres.map((genre, idx) => (
                                        <span
                                            key={idx}
                                            style={{
                                                padding: '0.25rem 0.75rem',
                                                backgroundColor: '#27272a',
                                                border: '1px solid #3f3f46',
                                                borderRadius: '9999px',
                                                fontSize: '0.75rem',
                                                color: '#a1a1aa'
                                            }}
                                        >
                                            {genre}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}


                        <div style={{ paddingTop: '1rem', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
                            <h4 style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#71717a', marginBottom: '0.5rem' }}>
                                Learn More
                            </h4>
                            <div style={{ display: 'flex', gap: '0.75rem' }}>
                                <a
                                    href={`https://www.wikidata.org/wiki/${book.qid}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: '0.5rem',
                                        padding: '0.5rem 0.75rem',
                                        backgroundColor: '#27272a',
                                        borderRadius: '8px',
                                        fontSize: '0.875rem',
                                        color: '#e4e4e7',
                                        textDecoration: 'none',
                                        transition: 'background-color 0.2s'
                                    }}
                                    onMouseEnter={e => e.currentTarget.style.backgroundColor = '#3f3f46'}
                                    onMouseLeave={e => e.currentTarget.style.backgroundColor = '#27272a'}
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                                        <polyline points="15 3 21 3 21 9" />
                                        <line x1="10" y1="14" x2="21" y2="3" />
                                    </svg>
                                    Wikidata
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>,
        document.body
    );
}
