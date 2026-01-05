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

export function ForceGraph({ data, width = 800, height = 600, onNodeClick }: ForceGraphProps) {
    const svgRef = useRef<SVGSVGElement>(null);
    const [nodes, setNodes] = useState<SimulationNode[]>([]);
    const [edges, setEdges] = useState<SimulationEdge[]>([]);
    const [hoveredNode, setHoveredNode] = useState<string | null>(null);
    const [transform, setTransform] = useState<d3.ZoomTransform>(d3.zoomIdentity);
    const simulationRef = useRef<d3.Simulation<SimulationNode, SimulationEdge> | null>(null);

    // Initialize simulation when data changes
    useEffect(() => {
        if (!data.nodes.length) return;

        // Create copies for simulation
        const simNodes: SimulationNode[] = data.nodes.map((n) => ({ ...n }));
        const simEdges: SimulationEdge[] = data.edges.map((e) => ({ ...e }));

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
    }, [data, width, height]);

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
        const isCentral = data.central_nodes.includes(node.id);
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
    }, [data.central_nodes]);

    // Get node radius based on centrality
    const getNodeRadius = useCallback((node: SimulationNode) => {
        const baseRadius = node.type === 'author' ? 12 : 8;
        const centralityBonus = (node.centrality || 0) * 10;
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

    if (!data.nodes.length) {
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
                <strong>{data.node_count}</strong> nodes · <strong>{data.edge_count}</strong> edges
            </div>

            {/* Legend */}
            <div
                style={{
                    position: 'absolute',
                    top: 'var(--spacing-4)',
                    right: 'var(--spacing-4)',
                    zIndex: 10,
                    background: 'var(--color-bg-elevated)',
                    padding: 'var(--spacing-3)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: 'var(--font-size-xs)',
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)', marginBottom: 'var(--spacing-1)' }}>
                    <span style={{ width: 12, height: 12, borderRadius: '50%', background: 'var(--color-node-author)' }} />
                    Author
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)' }}>
                    <span style={{ width: 14, height: 14, borderRadius: '50%', background: 'var(--color-accent)' }} />
                    High Centrality
                </div>
            </div>

            <svg
                ref={svgRef}
                width={width}
                height={height}
                style={{ background: 'var(--color-bg)', cursor: 'grab' }}
            >
                <g transform={`translate(${transform.x},${transform.y}) scale(${transform.k})`}>
                    {/* Edges */}
                    {edges.map((edge, i) => {
                        const source = edge.source as SimulationNode;
                        const target = edge.target as SimulationNode;
                        if (!source.x || !source.y || !target.x || !target.y) return null;

                        const isHovered = hoveredNode && (source.id === hoveredNode || target.id === hoveredNode);

                        return (
                            <g key={`edge-${i}`}>
                                <line
                                    className="graph-edge"
                                    x1={source.x}
                                    y1={source.y}
                                    x2={target.x}
                                    y2={target.y}
                                    stroke={getEdgeColor(edge)}
                                    strokeWidth={isHovered ? 2 : 1}
                                    opacity={isHovered ? 1 : 0.6}
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
                                        {edge.type.toLowerCase().replace('_', ' ')}
                                    </text>
                                )}
                            </g>
                        );
                    })}

                    {/* Nodes */}
                    {nodes.map((node) => (
                        <g
                            key={node.id}
                            className="graph-node"
                            transform={`translate(${node.x || 0},${node.y || 0})`}
                            onMouseEnter={() => setHoveredNode(node.id)}
                            onMouseLeave={() => setHoveredNode(null)}
                            onClick={() => onNodeClick?.(node)}
                            style={{ cursor: 'pointer' }}
                        >
                            <circle
                                r={getNodeRadius(node)}
                                fill={getNodeColor(node)}
                                stroke={hoveredNode === node.id ? 'white' : 'none'}
                                strokeWidth={2}
                            />
                            <text
                                className="graph-node__label"
                                dy={getNodeRadius(node) + 14}
                                textAnchor="middle"
                                style={{ opacity: hoveredNode === node.id || data.central_nodes.includes(node.id) ? 1 : 0.7 }}
                            >
                                {node.label.length > 20 ? node.label.slice(0, 18) + '...' : node.label}
                            </text>
                        </g>
                    ))}
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
