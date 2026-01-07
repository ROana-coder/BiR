/**
 * Books Force-Directed Graph Component
 * Visualizes relationships between Authors and their Books
 * (Star graph topology: Author -> Books)
 */

import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import * as d3 from 'd3';
import type { Book, GraphNode, GraphEdge } from '../types';

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

    // Drag Handling
    const handleDragStart = useCallback((event: any, node: SimulationNode) => {
        if (!simulationRef.current) return;
        if (!event.active) simulationRef.current.alphaTarget(0.3).restart();
        node.fx = node.x;
        node.fy = node.y;
    }, []);

    const handleDrag = useCallback((event: any, node: SimulationNode) => {
        node.fx = event.x;
        node.fy = event.y;
    }, []);

    const handleDragEnd = useCallback((event: any, node: SimulationNode) => {
        if (!simulationRef.current) return;
        if (!event.active) simulationRef.current.alphaTarget(0);
        node.fx = null;
        node.fy = null;
    }, []);

    if (!graphData.nodes.length) {
        return <div className="text-gray-500 text-center p-10">No books to visualize. Filter some search results first!</div>;
    }

    return (
        <div className="relative border border-white/10 rounded-lg overflow-hidden" style={{ width, height }}>
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
                                stroke="rgba(255,255,255,0.2)"
                                strokeWidth={1}
                            />
                        );
                    })}

                    {nodes.map((node) => (
                        <g
                            key={node.id}
                            transform={`translate(${node.x},${node.y})`}
                            onMouseEnter={() => setHoveredNode(node.id)}
                            onMouseLeave={() => setHoveredNode(null)}
                            onClick={() => onNodeClick && onNodeClick(node)}
                            className="cursor-pointer"
                        >
                            <circle
                                r={node.type === 'author' ? 8 : 6}
                                fill={node.type === 'author' ? '#ef4444' : '#22c55e'} // Red for Author, Green for Book
                                stroke={hoveredNode === node.id ? '#fff' : 'none'}
                                strokeWidth={2}
                            />
                            {/* Simple Label */}
                            <text
                                dy={node.type === 'author' ? 14 : 12}
                                textAnchor="middle"
                                fill="rgba(255,255,255,0.8)"
                                fontSize={node.type === 'author' ? 10 : 8}
                                className="pointer-events-none select-none"
                            >
                                {node.label.length > 15 && hoveredNode !== node.id ? node.label.slice(0, 12) + '...' : node.label}
                            </text>

                            {/* Detailed Tooltip on Hover */}
                            {hoveredNode === node.id && (
                                <g transform="translate(10, -20)">
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
                    ))}
                </g>
            </svg>
        </div>
    );
}
