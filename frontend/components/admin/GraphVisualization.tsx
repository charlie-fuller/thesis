'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { apiGet } from '@/lib/api';
import { logger } from '@/lib/logger';
import LoadingSpinner from '../LoadingSpinner';

// Dynamically import ForceGraph2D to avoid SSR issues
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <LoadingSpinner size="lg" />
    </div>
  ),
});

// Node color scheme by type
const NODE_COLORS: Record<string, string> = {
  Agent: '#a855f7',       // purple
  Document: '#3b82f6',    // blue
  Chunk: '#6366f1',       // indigo
  Conversation: '#22c55e', // green
  Message: '#10b981',     // emerald
  Stakeholder: '#f59e0b', // amber
  Meeting: '#ef4444',     // red
  Expertise: '#ec4899',   // pink
  Client: '#06b6d4',      // cyan
  User: '#8b5cf6',        // violet
  Topic: '#f97316',       // orange
  MeetingRoom: '#dc2626', // red-600
};

const DEFAULT_COLOR = '#6b7280'; // gray

interface GraphNode {
  id: string;
  neo4jId?: number;
  label: string;
  name: string;
  properties: Record<string, unknown>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number;
  fy?: number;
  [key: string]: unknown;
}

interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  type: string;
  [key: string]: unknown;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  total_nodes: number;
  total_links: number;
}

interface GraphVisualizationProps {
  onNodeSelect?: (node: GraphNode | null) => void;
  selectedNode?: GraphNode | null;
  visibleNodeTypes?: Set<string>;
}

export default function GraphVisualization({
  onNodeSelect,
  selectedNode,
  visibleNodeTypes,
}: GraphVisualizationProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Fetch graph data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiGet<GraphData>('/api/graph/visualization');
        setGraphData(data);
      } catch (err) {
        logger.error('Failed to fetch graph data:', err);
        setError('Failed to load graph data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Handle container resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height: Math.max(height, 400) });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Filter data based on visible node types
  const filteredData = useCallback(() => {
    if (!graphData) return { nodes: [], links: [] };
    if (!visibleNodeTypes || visibleNodeTypes.size === 0) return graphData;

    const filteredNodes = graphData.nodes.filter(n => visibleNodeTypes.has(n.label));
    const nodeIds = new Set(filteredNodes.map(n => n.id));

    const filteredLinks = graphData.links.filter(l => {
      const sourceId = typeof l.source === 'string' ? l.source : l.source.id;
      const targetId = typeof l.target === 'string' ? l.target : l.target.id;
      return nodeIds.has(sourceId) && nodeIds.has(targetId);
    });

    return { nodes: filteredNodes, links: filteredLinks };
  }, [graphData, visibleNodeTypes]);

  // Node click handler
  const handleNodeClick = useCallback((node: GraphNode, event: MouseEvent) => {
    onNodeSelect?.(node);
  }, [onNodeSelect]);

  // Node canvas drawing
  const nodeCanvasObject = useCallback((node: GraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.name || node.label;
    const fontSize = 12 / globalScale;
    const nodeColor = NODE_COLORS[node.label] || DEFAULT_COLOR;
    const isSelected = selectedNode?.id === node.id;
    const nodeSize = isSelected ? 8 : 6;

    // Draw node circle
    ctx.beginPath();
    ctx.arc(node.x || 0, node.y || 0, nodeSize, 0, 2 * Math.PI);
    ctx.fillStyle = nodeColor;
    ctx.fill();

    // Draw selection ring
    if (isSelected) {
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2 / globalScale;
      ctx.stroke();
    }

    // Draw label (only when zoomed in enough)
    if (globalScale > 0.7) {
      ctx.font = `${fontSize}px Sans-Serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#e5e5e5';
      ctx.fillText(label.slice(0, 20), node.x || 0, (node.y || 0) + nodeSize + fontSize);
    }
  }, [selectedNode]);

  // Reset zoom handler
  const handleResetZoom = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
    }
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-card rounded-lg">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="text-secondary mt-4">Loading graph data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full bg-card rounded-lg">
        <div className="text-center text-red-400">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const data = filteredData();

  return (
    <div ref={containerRef} className="relative w-full h-full bg-card rounded-lg overflow-hidden">
      {/* Controls overlay */}
      <div className="absolute top-4 right-4 z-10 flex gap-2">
        <button
          onClick={handleResetZoom}
          className="px-3 py-1.5 bg-hover hover:bg-border text-primary text-sm rounded-md transition-colors"
        >
          Reset View
        </button>
      </div>

      {/* Graph */}
      <ForceGraph2D
        ref={graphRef}
        graphData={data}
        width={dimensions.width}
        height={dimensions.height}
        nodeId="id"
        nodeCanvasObject={nodeCanvasObject as any}
        nodePointerAreaPaint={((node: any, color: string, ctx: CanvasRenderingContext2D) => {
          ctx.beginPath();
          ctx.arc(node.x || 0, node.y || 0, 10, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }) as any}
        linkColor={() => '#4b5563'}
        linkWidth={1}
        linkDirectionalParticles={0}
        onNodeClick={handleNodeClick as any}
        onBackgroundClick={() => onNodeSelect?.(null)}
        cooldownTicks={100}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
      />

      {/* Stats overlay */}
      <div className="absolute bottom-4 left-4 z-10 text-xs text-secondary bg-card/80 px-3 py-2 rounded">
        {data.nodes.length} nodes / {data.links.length} relationships
      </div>
    </div>
  );
}

// Export node colors for use in other components
export { NODE_COLORS };
