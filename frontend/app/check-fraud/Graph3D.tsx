'use client';

import dynamic from 'next/dynamic';
import { useState, useMemo, useRef, useEffect } from 'react';
import type { FraudRing } from '@/app/client/api';
import type { GraphNode, GraphEdge } from './types';
import { SCORE_COLOR_MAP } from './types';

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center text-white/50 text-sm">
      Loading 3D graph…
    </div>
  ),
});

interface Graph3DProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  fraudRings?: FraudRing[];
  selectedNode: GraphNode | null;
  onSelect: (n: GraphNode | null) => void;
  suspiciousOnly: boolean;
}

export function Graph3D({
  nodes: nodesProp,
  edges: edgesProp,
  selectedNode,
  onSelect,
  suspiciousOnly,
}: Graph3DProps) {
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [size, setSize] = useState({ w: 800, h: 460 });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onMove = (e: MouseEvent) => setTooltipPos({ x: e.clientX, y: e.clientY });
    el.addEventListener('mousemove', onMove);
    return () => el.removeEventListener('mousemove', onMove);
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const { width, height } = entries[0]?.contentRect ?? { width: 800, height: 460 };
      setSize({ w: Math.max(300, width), h: Math.max(300, height) });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const selectedId = selectedNode?.id ?? null;
  const baseNodes = suspiciousOnly ? nodesProp.filter((n) => n.color !== 'normal') : nodesProp;
  const connectedToSelected = selectedId
    ? new Set(
        edgesProp
          .filter((e) => e.from === selectedId || e.to === selectedId)
          .flatMap((e) => [e.from, e.to])
      )
    : new Set<string>();
  const visibleNodes =
    selectedId && connectedToSelected.size > 0
      ? [
          ...baseNodes,
          ...nodesProp.filter(
            (n) => connectedToSelected.has(n.id) && !baseNodes.some((b) => b.id === n.id)
          ),
        ]
      : baseNodes;
  const visibleEdges = edgesProp.filter(
    (e) =>
      visibleNodes.some((n) => n.id === e.from) && visibleNodes.some((n) => n.id === e.to)
  );

  const scoresWithValues = visibleNodes.map((n) => n.score).filter((s): s is number => s != null);
  const minScore = scoresWithValues.length ? Math.min(...scoresWithValues) : 0;
  const maxScore = scoresWithValues.length ? Math.max(...scoresWithValues) : 100;
  const scoreRange = Math.max(maxScore - minScore, 0.001);

  const graphData = useMemo(() => {
    const nodes = visibleNodes.map((n) => ({ ...n }));
    const nodeById = new Map(nodes.map((n) => [n.id, n]));
    const links = visibleEdges
      .map((e) => {
        const src = nodeById.get(e.from);
        const tgt = nodeById.get(e.to);
        if (!src || !tgt) return null;
        const connectedToSelected =
          selectedId !== null && (e.from === selectedId || e.to === selectedId);
        return {
          source: src,
          target: tgt,
          connectedToSelected,
        };
      })
      .filter((l): l is { source: GraphNode; target: GraphNode; connectedToSelected: boolean } => l != null);
    return { nodes, links };
  }, [visibleNodes, visibleEdges, selectedId]);

  const nodeColor = (node: GraphNode & { fillColor?: string }) =>
    node.fillColor ?? SCORE_COLOR_MAP[node.color] ?? '#22c55e';

  const nodeVal = (node: GraphNode) => {
    if (node.score == null) return 2;
    const t = (node.score - minScore) / scoreRange;
    return 2 + t * 4;
  };

  const linkColor = (link: { connectedToSelected?: boolean }) =>
    link.connectedToSelected ? '#00e87b' : 'rgba(255,255,255,0.35)';

  const linkWidth = (link: { connectedToSelected?: boolean }) =>
    link.connectedToSelected ? 1.5 : 0.8;

  const linkDirectionalParticles = (link: { connectedToSelected?: boolean }) =>
    link.connectedToSelected ? 8 : 2;

  const linkDirectionalParticleWidth = (link: { connectedToSelected?: boolean }) =>
    link.connectedToSelected ? 0.8 : 0.5;

  return (
    <div ref={containerRef} className="relative h-full w-full overflow-hidden rounded-xl">
      <ForceGraph3D
        graphData={graphData}
        width={size.w}
        height={size.h}
        nodeId="id"
        linkSource="source"
        linkTarget="target"
        nodeColor={nodeColor}
        nodeVal={nodeVal}
        nodeLabel={(n) => {
          const node = n as GraphNode;
          return `${node.id}${node.score != null ? ` (${node.score.toFixed(1)})` : ''}`;
        }}
        linkColor={linkColor}
        linkWidth={linkWidth}
        linkDirectionalParticles={linkDirectionalParticles}
        linkDirectionalParticleWidth={linkDirectionalParticleWidth}
        linkDirectionalParticleSpeed={0.02}
        linkDirectionalParticleColor={(link) =>
          (link as { connectedToSelected?: boolean }).connectedToSelected ? '#00e87b' : 'rgba(255,255,255,0.5)'
        }
        backgroundColor="#0a0d12"
        onNodeClick={(node, ev) => {
          const n = node as GraphNode;
          onSelect(selectedId === n.id ? null : n);
        }}
        onNodeHover={(node) => setHoveredNode((node as GraphNode) ?? null)}
        onBackgroundClick={() => onSelect(null)}
        enableNodeDrag
        enableNavigationControls
        showNavInfo={false}
      />
      {hoveredNode && (
        <div
          className="pointer-events-none fixed z-30 rounded-lg border border-white/20 bg-[#0f1419]/95 backdrop-blur px-3 py-2.5 shadow-xl text-left min-w-[160px]"
          style={{ left: tooltipPos.x + 14, top: tooltipPos.y + 14 }}
        >
          <div className="text-[10px] font-bold uppercase tracking-wider text-white/50 mb-1.5">Node</div>
          <div className="text-sm font-semibold text-white">{hoveredNode.id}</div>
          {hoveredNode.score != null && (
            <div
              className="text-xs font-medium mt-0.5"
              style={{ color: hoveredNode.fillColor ?? SCORE_COLOR_MAP[hoveredNode.color] }}
            >
              Score: {hoveredNode.score.toFixed(1)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
