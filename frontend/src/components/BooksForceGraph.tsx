/**
 * Star graph topology: Author -> Books
 */

import { useEffect, useRef, useState, useMemo } from 'react';
import * as d3 from 'd3';
import type { Book } from '../types';

interface BooksForceGraphProps {
    books: Book[];
    width?: number;
    height?: number;
    onNodeClick?: (node: any) => void;
}

interface SimulationNode extends d3.SimulationNodeDatum {
    id: string;
    label: string;
    type: 'author' | 'book';
    data?: any; // Original Book or Author data
    x?: number;
    y?: number;
    fx?: number | null;
    fy?: number | null;
}

interface SimulationEdge extends d3.SimulationLinkDatum<SimulationNode> {
    source: string | SimulationNode;
    target: string | SimulationNode;
    type: string;
}

export function BooksForceGraph({ books, width = 800, height = 600, onNodeClick }: BooksForceGraphProps) {
    const svgRef = useRef<SVGSVGElement>(null);
    const [nodes, setNodes] = useState<SimulationNode[]>([]);
    const [edges, setEdges] = useState<SimulationEdge[]>([]);
    const [hoveredNode, setHoveredNode] = useState<string | null>(null);
    const [transform, setTransform] = useState<d3.ZoomTransform>(d3.zoomIdentity);
    const simulationRef = useRef<d3.Simulation<SimulationNode, SimulationEdge> | null>(null);

    // Process data into nodes and edges
    const graphData = useMemo(() => {
        const nodesMap = new Map<string, SimulationNode>();
        const edgesList: SimulationEdge[] = [];

        books.forEach(book => {
            // Book Node
            if (!nodesMap.has(book.qid)) {
                nodesMap.set(book.qid, {
                    id: book.qid,
                    label: book.title,
                    type: 'book',
                    data: book
                });
            }

            // Author Nodes & Edges
            book.author_qids.forEach((authorQid, idx) => {
                const authorName = book.authors[idx] || 'Unknown Author';

                if (!nodesMap.has(authorQid)) {
                    nodesMap.set(authorQid, {
                        id: authorQid,
                        label: authorName,
                        type: 'author',
                        data: { name: authorName }
                    });
                }

                edgesList.push({
                    source: authorQid,
                    target: book.qid,
                    type: 'authored'
                });
            });
        });

        return { nodes: Array.from(nodesMap.values()), edges: edgesList };
    }, [books]);

    // Initialize/Update Simulation
    useEffect(() => {
        if (!graphData.nodes.length) return;

        // Clone for mutation
        const simNodes = graphData.nodes.map(n => ({ ...n }));
        const simEdges = graphData.edges.map(e => ({ ...e }));

        if (simulationRef.current) simulationRef.current.stop();

        const simulation = d3.forceSimulation<SimulationNode>(simNodes)
            .force('link', d3.forceLink<SimulationNode, SimulationEdge>(simEdges).id(d => d.id).distance(80))
            .force('charge', d3.forceManyBody().strength(-200))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collide', d3.forceCollide().radius(20));

        simulation.on('tick', () => {
            setNodes([...simNodes]);
            setEdges([...simEdges]);
        });

        simulationRef.current = simulation;

        return () => { simulation.stop(); };
    }, [graphData, width, height]);

    // Zoom Handling
    useEffect(() => {
        if (!svgRef.current) return;
        const svg = d3.select(svgRef.current);
        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => setTransform(event.transform));
        svg.call(zoom);
        return () => { svg.on('.zoom', null); };
    }, []);




    if (!graphData.nodes.length) {
        return <div className="text-gray-500 text-center p-10">No books to visualize. Filter some search results first!</div>;
    }

    return (
        <div className="relative border border-white/10 rounded-lg overflow-hidden" style={{ width, height }}>
            <div
                style={{
                    position: 'absolute',
                    top: 50,
                    left: 'var(--spacing-4)',
                    zIndex: 10,
                    background: 'var(--color-bg-elevated)',
                    padding: 'var(--spacing-3)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: 'var(--font-size-sm)',
                }}
            >
                <strong>{graphData.nodes.length}</strong> nodes (<strong>{graphData.nodes.filter(n => n.type === 'author').length}</strong> authors, <strong>{graphData.nodes.filter(n => n.type === 'book').length}</strong> books)
            </div>

            <div
                style={{
                    position: 'absolute',
                    top: 12,
                    right: 12,
                    zIndex: 10,
                    background: 'rgba(24, 24, 27, 0.95)',
                    padding: '10px 12px',
                    borderRadius: 8,
                    fontSize: 13,
                    border: '1px solid rgba(63, 63, 70, 0.8)'
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <div style={{ width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <svg width="22" height="22" viewBox="0 0 24 24">
                            <circle cx="12" cy="12" r="10" fill="#ef4444" opacity="0.9" />
                            <circle cx="12" cy="9" r="3" fill="white" opacity="0.9" />
                            <path d="M6,20 Q6,14 12,14 Q18,14 18,20" fill="white" opacity="0.9" />
                        </svg>
                    </div>
                    <span style={{ color: 'rgba(255,255,255,0.9)' }}>Author</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <svg width="22" height="22" viewBox="0 0 24 24">
                            <rect x="4" y="2" width="16" height="20" rx="2" fill="#22c55e" />
                            <rect x="4" y="2" width="4" height="20" fill="rgba(0,0,0,0.2)" />
                            <line x1="10" y1="7" x2="18" y2="7" stroke="white" strokeWidth="1.5" opacity="0.6" />
                            <line x1="10" y1="11" x2="18" y2="11" stroke="white" strokeWidth="1.5" opacity="0.6" />
                            <line x1="10" y1="15" x2="18" y2="15" stroke="white" strokeWidth="1.5" opacity="0.6" />
                        </svg>
                    </div>
                    <span style={{ color: 'rgba(255,255,255,0.9)' }}>Book</span>
                </div>
            </div>

            <svg ref={svgRef} width={width} height={height} className="bg-zinc-950 cursor-grab active:cursor-grabbing">
                <g transform={`translate(${transform.x},${transform.y}) scale(${transform.k})`}>
                    {edges.map((edge, i) => {
                        const source = edge.source as SimulationNode;
                        const target = edge.target as SimulationNode;
                        if (!source.x || !target.x) return null;
                        return (
                            <line
                                key={i}
                                x1={source.x} y1={source.y}
                                x2={target.x} y2={target.y}
                                stroke="rgba(94, 234, 212, 0.5)"
                                strokeWidth={1.5}
                            />
                        );
                    })}

                    {nodes.map((node) => {
                        const isHovered = hoveredNode === node.id;
                        const radius = node.type === 'author' ? 16 : 14;

                        return (
                            <g
                                key={node.id}
                                transform={`translate(${node.x},${node.y})`}
                                onMouseEnter={() => setHoveredNode(node.id)}
                                onMouseLeave={() => setHoveredNode(null)}
                                onClick={() => onNodeClick && onNodeClick(node)}
                                className="cursor-pointer"
                            >
                                {node.type === 'author' ? (
                                    /* Person icon for authors */
                                    <g>
                                        <circle
                                            r={radius}
                                            fill="#ef4444"
                                            stroke={isHovered ? '#fff' : 'transparent'}
                                            strokeWidth={2}
                                            opacity={0.9}
                                        />
                                        <g transform={`scale(${radius / 14})`}>
                                            <circle cx="0" cy="-4" r="4" fill="white" opacity="0.9" />
                                            <path
                                                d="M-6,8 Q-6,2 0,2 Q6,2 6,8 L6,10 L-6,10 Z"
                                                fill="white"
                                                opacity="0.9"
                                            />
                                        </g>
                                    </g>
                                ) : (
                                    /* Book icon */
                                    <g transform={`scale(${radius / 10})`}>
                                        <rect
                                            x="-7"
                                            y="-9"
                                            width="14"
                                            height="18"
                                            rx="1"
                                            fill="#22c55e"
                                            stroke={isHovered ? 'white' : 'transparent'}
                                            strokeWidth={isHovered ? 2 : 0}
                                        />
                                        <rect x="-7" y="-9" width="3" height="18" fill="rgba(0,0,0,0.2)" />
                                        <line x1="-2" y1="-5" x2="5" y2="-5" stroke="white" strokeWidth="1" opacity="0.6" />
                                        <line x1="-2" y1="-2" x2="5" y2="-2" stroke="white" strokeWidth="1" opacity="0.6" />
                                        <line x1="-2" y1="1" x2="5" y2="1" stroke="white" strokeWidth="1" opacity="0.6" />
                                    </g>
                                )}


                                <text
                                    dy={radius + 10}
                                    textAnchor="middle"
                                    fill="rgba(255,255,255,0.8)"
                                    fontSize={node.type === 'author' ? 10 : 8}
                                    className="pointer-events-none select-none"
                                >
                                    {node.label.length > 15 && !isHovered ? node.label.slice(0, 12) + '...' : node.label}
                                </text>


                                {isHovered && (
                                    <g transform="translate(15, -25)">
                                        <rect
                                            x={0} y={-20} width={180} height={node.type === 'book' ? 60 : 40}
                                            fill="#18181b" stroke="#3f3f46" rx={4}
                                        />
                                        <text x={10} y={0} fill="#fff" fontSize={11} fontWeight="bold">{node.label}</text>
                                        <text x={10} y={14} fill="#a1a1aa" fontSize={9}>
                                            {node.type === 'book' ? (
                                                <>
                                                    📅 {(node.data as Book)?.publication_year || 'Unknown'}
                                                    • 📖 {((node.data as Book)?.genres && (node.data as Book).genres.length > 0
                                                        ? (node.data as Book).genres.join(', ')
                                                        : (node.data as Book)?.genre) || 'Genre N/A'}
                                                </>
                                            ) : (
                                                <>✍️ Filtered Author</>
                                            )}
                                        </text>
                                    </g>
                                )}
                            </g>
                        );
                    })}
                </g>
            </svg>
        </div>
    );
}
