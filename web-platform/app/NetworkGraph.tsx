"use client";

import { useEffect, useState, useRef } from "react";
import dynamic from "next/dynamic";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
});

export default function NetworkGraph() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [containerWidth, setContainerWidth] = useState(800);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/data")
      .then((res) => res.json())
      .then((data) => {
        if (data.graph && data.graph.nodes.length > 0) {
          setGraphData(data.graph);
        } else {
          setGraphData({ nodes: [], links: [] });
        }
      })
      .catch((err) => console.error("Failed to fetch graph data:", err));

    if (containerRef.current) {
      setContainerWidth(containerRef.current.clientWidth);
    }
  }, []);

  return (
    <div 
      ref={containerRef} 
      className="w-full h-[600px] border border-gray-200 rounded-lg overflow-hidden bg-gray-50 shadow-inner"
    >
      {graphData.nodes.length > 0 ? (
        <ForceGraph2D
          width={containerWidth}
          height={600}
          graphData={graphData}
          backgroundColor="#f8fafc"
          
          // 1. DRAW CUSTOM NODES WITH TEXT
          nodeCanvasObject={(node: any, ctx, globalScale) => {
            const label = node.label;
            const fontSize = 12/globalScale; // Scale font so it stays readable on zoom
            const radius = 5; 

            // A. Draw the Circle (Node)
            ctx.beginPath();
            ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
            ctx.fillStyle = node.type === "book" ? "#0d9488" : "#ef4444"; // Teal vs Red
            ctx.fill();

            // B. Draw the Text Label
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = "#333"; // Text Color
            
            // Draw text slightly below the node
            ctx.fillText(label, node.x, node.y + radius + fontSize); 
          }}
          
          nodeRelSize={6}
          linkColor={() => "#cbd5e1"}
          cooldownTicks={100}
        />
      ) : (
        <div className="flex h-full items-center justify-center text-gray-400">
          Waiting for data... (Click Sync)
        </div>
      )}
    </div>
  );
}