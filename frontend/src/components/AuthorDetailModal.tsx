import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { Author } from '../types';
import { getAuthor } from '../api/client';

interface AuthorDetailModalProps {
    qid: string;
    onClose: () => void;
}

export function AuthorDetailModal({ qid, onClose }: AuthorDetailModalProps) {
    const [author, setAuthor] = useState<Author | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchDetails = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await getAuthor(qid);
                setAuthor(data);
            } catch (err) {
                console.error('Failed to fetch author details:', err);
                // Use the error message from the mocked backend response if available, or generic
                setError(err instanceof Error ? err.message : 'Failed to load author details.');
            } finally {
                setLoading(false);
            }
        };

        if (qid) {
            fetchDetails();
        }
    }, [qid]);

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
                className="bg-zinc-900 border border-white/10 rounded-xl shadow-2xl relative"
                style={{
                    width: '100%',
                    maxWidth: '48rem',
                    maxHeight: '80vh',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'row',
                    backgroundColor: '#18181b',
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


                {loading ? (
                    <div className="p-12 text-center text-zinc-400 w-full">Loading author details...</div>
                ) : error ? (
                    <div className="p-12 text-center text-red-400 w-full">
                        <p className="font-bold mb-2">Error</p>
                        <p className="text-sm opacity-80">{error}</p>
                    </div>
                ) : author ? (
                    <>

                        {author.image_url ? (
                            <div style={{ width: '40%', minWidth: '300px', position: 'relative' }}>
                                <img
                                    src={author.image_url}
                                    alt={author.name}
                                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                />
                            </div>
                        ) : null}


                        <div style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
                            <div className="mb-6">
                                <h2 className="text-3xl font-bold text-white mb-2">{author.name}</h2>
                                <div className="flex gap-2 text-sm text-zinc-400 pb-4 border-b border-white/10">
                                    {author.birth_date && <span>Born: {author.birth_date}</span>}
                                    {author.death_date && <span>• Died: {author.death_date}</span>}
                                </div>
                            </div>

                            <div className="space-y-6">
                                {author.nationality && (
                                    <div>
                                        <h4 className="text-xs uppercase tracking-wider text-zinc-500 mb-1">Nationality</h4>
                                        <span className="text-zinc-200">{author.nationality}</span>
                                    </div>
                                )}

                                {author.description && (
                                    <div>
                                        <h4 className="text-xs uppercase tracking-wider text-zinc-500 mb-1">Description</h4>
                                        <p className="text-zinc-300 leading-relaxed">{author.description}</p>
                                    </div>
                                )}


                                <div className="pt-4 border-t border-white/10">
                                    <h4 className="text-xs uppercase tracking-wider text-zinc-500 mb-2">Learn More</h4>
                                    <div className="flex gap-3">
                                        <a
                                            href={`https://www.wikidata.org/wiki/${qid}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center gap-2 px-3 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm text-zinc-200 transition-colors"
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
                    </>
                ) : null}
            </div>
        </div>,
        document.body
    );
}
