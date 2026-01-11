/**
 * Force-Directed Graph Component
 * Uses D3 for calculation and React for rendering
 * Visualizes author relationships and influence networks
 */

import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import * as d3 from 'd3';
import type { GraphData, GraphNode, GraphEdge } from '../types';

interface ForceGraphProps {
    data: GraphData;
    width?: number;
    height?: number;
    onNodeClick?: (node: GraphNode) => void;
    highlightedNodeIds?: string[];
    /** Map of author QID to author name for adding missing nodes */
    authorNames?: Map<string, string>;
}

interface SimulationNode extends GraphNode {
    x?: number;
    y?: number;
    vx?: number;
    vy?: number;
    fx?: number | null;
    fy?: number | null;
}

interface SimulationEdge extends GraphEdge {
    source: SimulationNode | string;
    target: SimulationNode | string;
}

export function ForceGraph({ data, width = 800, height = 600, onNodeClick, highlightedNodeIds, authorNames }: ForceGraphProps) {
    const svgRef = useRef<SVGSVGElement>(null);
    const [nodes, setNodes] = useState<SimulationNode[]>([]);
    const [edges, setEdges] = useState<SimulationEdge[]>([]);
    const [hoveredNode, setHoveredNode] = useState<string | null>(null);
    const [transform, setTransform] = useState<d3.ZoomTransform>(d3.zoomIdentity);
    const simulationRef = useRef<d3.Simulation<SimulationNode, SimulationEdge> | null>(null);

    // Filter graph data to only include nodes from query results, and add missing authors
    const filteredData = useMemo(() => {
        if (!highlightedNodeIds || highlightedNodeIds.length === 0) {
            return data;
        }

        const allowedNodeIds = new Set(highlightedNodeIds);

        // Start with nodes from the graph data that are in the query results
        const filteredNodes: GraphNode[] = data.nodes.filter(node => allowedNodeIds.has(node.id));
        const existingNodeIds = new Set(filteredNodes.map(n => n.id));

        // Add missing authors as isolated nodes (authors in query results but not in graph data)
        if (authorNames) {
            for (const qid of highlightedNodeIds) {
                if (!existingNodeIds.has(qid)) {
                    const name = authorNames.get(qid);
                    // Use the name if available and it's not just a QID
                    const label = name && !name.startsWith('Q') ? name : `Unknown (${qid})`;
                    filteredNodes.push({
                        id: qid,
                        label,
                        type: 'author' as const,
                        metadata: {},
                        centrality: null,
                        degree: null,
                    });
                }
            }
        }

        const filteredNodeIds = new Set(filteredNodes.map(n => n.id));

        // Filter edges to only include those between filtered nodes
        const filteredEdges = data.edges.filter(edge =>
            filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target)
        );

        // Update central_nodes to only include filtered ones
        const filteredCentralNodes = data.central_nodes.filter(id => filteredNodeIds.has(id));

        return {
            nodes: filteredNodes,
            edges: filteredEdges,
            node_count: filteredNodes.length,
            edge_count: filteredEdges.length,
            central_nodes: filteredCentralNodes,
        };
    }, [data, highlightedNodeIds, authorNames]);

    // Initialize simulation when data changes
    useEffect(() => {
        if (!filteredData.nodes.length) return;

        // Create copies for simulation
        const simNodes: SimulationNode[] = filteredData.nodes.map((n) => ({ ...n }));
        const simEdges: SimulationEdge[] = filteredData.edges.map((e) => ({ ...e }));

        // Stop previous simulation
        if (simulationRef.current) {
            simulationRef.current.stop();
        }

        // Create force simulation
        const simulation = d3
            .forceSimulation<SimulationNode>(simNodes)
            .force(
                'link',
                d3
                    .forceLink<SimulationNode, SimulationEdge>(simEdges)
                    .id((d) => d.id)
                    .distance(100)
            )
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(30));

        simulation.on('tick', () => {
            setNodes([...simNodes]);
            setEdges([...simEdges]);
        });

        simulationRef.current = simulation;

        return () => {
            simulation.stop();
        };
    }, [filteredData, width, height]);

    // Setup zoom behavior
    useEffect(() => {
        if (!svgRef.current) return;

        const svg = d3.select(svgRef.current);
        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                setTransform(event.transform);
            });

        svg.call(zoom);

        return () => {
            svg.on('.zoom', null);
        };
    }, []);

    // Node drag handlers
    const handleDragStart = useCallback(
        (event: React.MouseEvent, node: SimulationNode) => {
            if (simulationRef.current) {
                simulationRef.current.alphaTarget(0.3).restart();
                node.fx = node.x;
                node.fy = node.y;
            }
        },
        []
    );

    const handleDrag = useCallback((event: React.MouseEvent, node: SimulationNode) => {
        // Calculate position accounting for zoom transform
        const [x, y] = transform.invert([event.nativeEvent.offsetX, event.nativeEvent.offsetY]);
        node.fx = x;
        node.fy = y;
        setNodes((prev) => [...prev]);
    }, [transform]);

    const handleDragEnd = useCallback((node: SimulationNode) => {
        if (simulationRef.current) {
            simulationRef.current.alphaTarget(0);
            node.fx = null;
            node.fy = null;
        }
    }, []);

    // Get node color based on type and centrality
    const getNodeColor = useCallback((node: SimulationNode) => {
        const isCentral = filteredData.central_nodes.includes(node.id);
        if (isCentral) return 'var(--color-accent)';

        switch (node.type) {
            case 'author':
                return 'var(--color-node-author)';
            case 'book':
                return 'var(--color-node-book)';
            case 'movement':
                return 'var(--color-node-movement)';
            default:
                return 'var(--color-text-secondary)';
        }
    }, [filteredData.central_nodes]);

    // Get node radius based on centrality
    const getNodeRadius = useCallback((node: SimulationNode) => {
        const baseRadius = node.type === 'author' ? 8 : 6;
        const centralityBonus = (node.centrality || 0) * 5;
        return baseRadius + centralityBonus;
    }, []);

    // Get edge style
    const getEdgeColor = useCallback((edge: SimulationEdge) => {
        const sourceId = typeof edge.source === 'string' ? edge.source : edge.source.id;
        const targetId = typeof edge.target === 'string' ? edge.target : edge.target.id;

        if (hoveredNode && (sourceId === hoveredNode || targetId === hoveredNode)) {
            return 'var(--color-accent)';
        }
        return 'var(--color-edge)';
    }, [hoveredNode]);

    if (!filteredData.nodes.length) {
        return (
            <div className="empty-state">
                <div className="empty-state__icon">🔗</div>
                <h3 className="empty-state__title">No Network Data</h3>
                <p className="empty-state__description">
                    Select authors to visualize their relationships and influence network.
                </p>
            </div>
        );
    }

    return (
        <div className="viz-container" style={{ position: 'relative' }}>
            {/* Graph Info */}
            <div
                style={{
                    position: 'absolute',
                    top: 'var(--spacing-4)',
                    left: 'var(--spacing-4)',
                    zIndex: 10,
                    background: 'var(--color-bg-elevated)',
                    padding: 'var(--spacing-3)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: 'var(--font-size-sm)',
                }}
            >
                <strong>{filteredData.node_count}</strong> nodes · <strong>{filteredData.edge_count}</strong> edges
            </div>

            {/* Legend */}
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
                            <circle cx="12" cy="12" r="10" fill="var(--color-node-author)" opacity="0.9" />
                            <circle cx="12" cy="9" r="3" fill="white" opacity="0.9" />
                            <path d="M6,20 Q6,14 12,14 Q18,14 18,20" fill="white" opacity="0.9" />
                        </svg>
                    </div>
                    <span style={{ color: 'rgba(255,255,255,0.9)' }}>Author</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <svg width="22" height="22" viewBox="0 0 24 24">
                            <circle cx="12" cy="12" r="10" fill="var(--color-accent)" opacity="0.9" />
                            <circle cx="12" cy="9" r="3" fill="white" opacity="0.9" />
                            <path d="M6,20 Q6,14 12,14 Q18,14 18,20" fill="white" opacity="0.9" />
                            <circle cx="18" cy="6" r="5" fill="gold" />
                            <text x="18" y="8" textAnchor="middle" fontSize="6" fill="black" fontWeight="bold">★</text>
                        </svg>
                    </div>
                    <span style={{ color: 'rgba(255,255,255,0.9)' }}>High Influence</span>
                </div>
            </div>

            <svg
                ref={svgRef}
                width={width}
                height={height}
                style={{ background: 'var(--color-bg)', cursor: 'grab' }}
            >
                <defs>
                    <marker
                        id="arrowhead"
                        viewBox="0 -5 10 10"
                        refX="8"
                        refY="0"
                        markerWidth="6"
                        markerHeight="6"
                        orient="auto"
                        fill="var(--color-edge)"
                    >
                        <path d="M0,-5L10,0L0,5" />
                    </marker>
                    <marker
                        id="arrowhead-hover"
                        viewBox="0 -5 10 10"
                        refX="8"
                        refY="0"
                        markerWidth="6"
                        markerHeight="6"
                        orient="auto"
                        fill="var(--color-accent)"
                    >
                        <path d="M0,-5L10,0L0,5" />
                    </marker>
                </defs>
                <g transform={`translate(${transform.x},${transform.y}) scale(${transform.k})`}>
                    {/* Edges */}
                    {edges.map((edge, i) => {
                        const source = edge.source as SimulationNode;
                        const target = edge.target as SimulationNode;
                        if (!source.x || !source.y || !target.x || !target.y) return null;

                        const isHovered = hoveredNode && (source.id === hoveredNode || target.id === hoveredNode);

                        // Calculate intersection with target node boundary
                        const dx = target.x - source.x;
                        const dy = target.y - source.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        const targetRadius = getNodeRadius(target);
                        const arrowPadding = 4; // Space for arrow

                        // Shorten line to stop at edge of node
                        const ratio = (distance - targetRadius - arrowPadding) / distance;
                        const endX = source.x + dx * ratio;
                        const endY = source.y + dy * ratio;

                        if (ratio < 0) return null; // Don't draw if nodes are overlapping

                        return (
                            <g key={`edge-${i}`}>
                                <line
                                    className="graph-edge"
                                    x1={source.x}
                                    y1={source.y}
                                    x2={endX}
                                    y2={endY}
                                    stroke={getEdgeColor(edge)}
                                    strokeWidth={isHovered ? 2 : 1}
                                    opacity={isHovered ? 1 : 0.6}
                                    markerEnd={edge.type === 'shared_movement' ? undefined : `url(#${isHovered ? 'arrowhead-hover' : 'arrowhead'})`}
                                />
                                {isHovered && (
                                    <text
                                        x={(source.x + target.x) / 2}
                                        y={(source.y + target.y) / 2}
                                        textAnchor="middle"
                                        fill="var(--color-text-primary)"
                                        fontSize="10px"
                                        style={{ background: 'var(--color-bg)', textShadow: '0 0 4px var(--color-bg)' }}
                                    >
                                        {edge.label || edge.type.toLowerCase().replace('_', ' ')}
                                    </text>
                                )}
                            </g>
                        );
                    })}

                    {/* Nodes */}
                    {nodes.map((node) => {
                        const radius = getNodeRadius(node);
                        const color = getNodeColor(node);
                        const isHovered = hoveredNode === node.id;
                        const isCentral = filteredData.central_nodes.includes(node.id);

                        return (
                            <g
                                key={node.id}
                                className="graph-node"
                                transform={`translate(${node.x || 0},${node.y || 0})`}
                                onMouseEnter={() => setHoveredNode(node.id)}
                                onMouseLeave={() => setHoveredNode(null)}
                                onClick={() => onNodeClick?.(node)}
                                style={{ cursor: 'pointer' }}
                            >
                                {node.type === 'author' ? (
                                    <g>
                                        <circle
                                            r={radius + 2}
                                            fill={color}
                                            stroke={isHovered ? 'white' : isCentral ? 'var(--color-accent-muted)' : 'transparent'}
                                            strokeWidth={isHovered ? 3 : isCentral ? 2 : 0}
                                            opacity={0.9}
                                        />
                                        {/* Person silhouette */}
                                        <g transform={`scale(${radius / 14})`}>
                                            <circle cx="0" cy="-4" r="4" fill="white" opacity="0.9" />
                                            <path d="M-6,8 Q-6,2 0,2 Q6,2 6,8 L6,10 L-6,10 Z" fill="white" opacity="0.9" />
                                        </g>
                                        {isCentral && (
                                            <g transform={`translate(${radius * 0.7}, ${-radius * 0.7})`}>
                                                <circle r="5" fill="gold" />
                                                <text textAnchor="middle" dy="3" fontSize="7" fill="black" fontWeight="bold">★</text>
                                            </g>
                                        )}
                                    </g>
                                ) : node.type === 'book' ? (
                                    <g>
                                        <g transform={`scale(${radius / 10})`}>
                                            <rect x="-7" y="-9" width="14" height="18" rx="1" fill={color} stroke={isHovered ? 'white' : 'transparent'} strokeWidth={isHovered ? 2 : 0} />
                                            <rect x="-7" y="-9" width="3" height="18" fill="rgba(0,0,0,0.2)" />
                                            <line x1="-2" y1="-5" x2="5" y2="-5" stroke="white" strokeWidth="1" opacity="0.6" />
                                            <line x1="-2" y1="-2" x2="5" y2="-2" stroke="white" strokeWidth="1" opacity="0.6" />
                                            <line x1="-2" y1="1" x2="5" y2="1" stroke="white" strokeWidth="1" opacity="0.6" />
                                        </g>
                                    </g>
                                ) : (
                                    <circle
                                        r={radius}
                                        fill={color}
                                        stroke={isHovered ? 'white' : 'none'}
                                        strokeWidth={2}
                                    />
                                )}
                                <text
                                    className="graph-node__label"
                                    dy={radius + 14}
                                    textAnchor="middle"
                                    style={{ opacity: isHovered || isCentral ? 1 : 0.7 }}
                                >
                                    {node.label.length > 20 ? node.label.slice(0, 18) + '...' : node.label}
                                </text>
                            </g>
                        );
                    })}
                </g>
            </svg>

            {/* Tooltip */}
            {hoveredNode && (
                <div
                    className="tooltip"
                    style={{
                        top: 'var(--spacing-16)',
                        left: '50%',
                        transform: 'translateX(-50%)',
                    }}
                >
                    {nodes.find((n) => n.id === hoveredNode)?.label}
                    <br />
                    <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)' }}>
                        Click to view details
                    </span>
                </div>
            )}
        </div>
    );
}
