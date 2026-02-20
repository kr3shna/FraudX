'use client';

import { useState, useRef, useEffect } from 'react';
import * as d3 from 'd3';
import type { FraudRing } from '@/app/client/api';
import type { GraphNode, GraphEdge } from './types';
import { SCORE_COLOR_MAP } from './types';
import { getScoreColorKey, convexHull } from './graphUtils';

interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  fraudRings?: FraudRing[];
  selectedNode: GraphNode | null;
  onSelect: (n: GraphNode | null) => void;
  suspiciousOnly: boolean;
  ringHighlight: boolean;
}

export function GraphCanvas({
  nodes: nodesProp,
  edges: edgesProp,
  fraudRings = [],
  selectedNode,
  onSelect,
  suspiciousOnly,
  ringHighlight,
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const hoverRef = useRef({ setHoveredNode, setTooltipPos });
  const onSelectRef = useRef(onSelect);
  const selectedNodeRef = useRef(selectedNode);
  hoverRef.current = { setHoveredNode, setTooltipPos };
  onSelectRef.current = onSelect;
  selectedNodeRef.current = selectedNode;

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const selectedId = selectedNode?.id ?? null;
    const baseNodes = suspiciousOnly ? nodesProp.filter((n) => n.color !== 'normal') : nodesProp;
    const connectedToSelected = selectedId
      ? new Set(
          edgesProp
            .filter((e) => e.from === selectedId || e.to === selectedId)
            .flatMap((e) => [e.from, e.to])
        )
      : new Set<string>();
    const expandedNodes =
      selectedId && connectedToSelected.size > 0
        ? [
            ...baseNodes,
            ...nodesProp.filter(
              (n) => connectedToSelected.has(n.id) && !baseNodes.some((b) => b.id === n.id)
            ),
          ]
        : baseNodes;
    const visibleNodes = expandedNodes;
    const visibleEdges = edgesProp.filter(
      (e) =>
        visibleNodes.some((n) => n.id === e.from) && visibleNodes.some((n) => n.id === e.to)
    );

    const width = 800;
    const height = 540;
    const duration = 200;
    const nodeRadiusBase = 10;
    const nodeRadiusMax = 18;
    const scoresWithValues = visibleNodes.map((n) => n.score).filter((s): s is number => s != null);
    const minScore = scoresWithValues.length ? Math.min(...scoresWithValues) : 0;
    const maxScore = scoresWithValues.length ? Math.max(...scoresWithValues) : 100;
    const scoreRange = Math.max(maxScore - minScore, 0.001);

    const simNodes = visibleNodes.map((n) => ({
      ...n,
      x: n.x + width / 2 - 400,
      y: n.y + height / 2 - 270,
    }));
    const nodeById = new Map(simNodes.map((n) => [n.id, n]));
    const simLinks = visibleEdges
      .map((e) => {
        const src = nodeById.get(e.from);
        const tgt = nodeById.get(e.to);
        if (!src || !tgt) return null;
        const connectedToSelected =
          selectedId !== null && (e.from === selectedId || e.to === selectedId);
        return { source: src, target: tgt, connectedToSelected };
      })
      .filter((l): l is { source: (typeof simNodes)[0]; target: (typeof simNodes)[0]; connectedToSelected: boolean } => l != null);

    const svg = d3
      .select(el)
      .append('svg')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('width', '100%')
      .attr('height', '100%')
      .style('display', 'block')
      .style('cursor', 'grab');

    const defs = svg.append('defs');
    defs
      .append('pattern')
      .attr('id', 'd3-grid')
      .attr('width', 40)
      .attr('height', 40)
      .attr('patternUnits', 'userSpaceOnUse')
      .append('path')
      .attr('d', 'M 40 0 L 0 0 0 40')
      .attr('fill', 'none')
      .attr('stroke', 'rgba(255,255,255,0.04)')
      .attr('stroke-width', 0.5);
    defs
      .append('marker')
      .attr('id', 'd3-arrow')
      .attr('markerWidth', 10)
      .attr('markerHeight', 10)
      .attr('refX', 8)
      .attr('refY', 5)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,0 L0,10 L10,5 z')
      .attr('fill', 'rgba(255,255,255,0.4)');
    defs
      .append('marker')
      .attr('id', 'd3-arrow-highlight')
      .attr('markerWidth', 12)
      .attr('markerHeight', 12)
      .attr('refX', 10)
      .attr('refY', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,0 L0,12 L12,6 z')
      .attr('fill', 'rgba(0,233,123,0.9)');
    const glowFilter = defs.append('filter').attr('id', 'd3-glow');
    glowFilter.append('feGaussianBlur').attr('stdDeviation', 4).attr('result', 'blur');
    glowFilter
      .append('feMerge')
      .selectAll('feMergeNode')
      .data(['blur', 'SourceGraphic'])
      .join('feMergeNode')
      .attr('in', (d) => d);

    const gZoom = svg.append('g').attr('class', 'zoom-group');
    gZoom.append('rect').attr('width', width).attr('height', height).attr('fill', 'url(#d3-grid)');
    const gLinks = gZoom.append('g').attr('class', 'links');
    const gRings = gZoom.append('g').attr('class', 'ring-hulls');
    const gNodes = gZoom.append('g').attr('class', 'nodes');

    const lineGen = d3.line<{ x: number; y: number }>().x((d) => d.x).y((d) => d.y);

    const linkPaths = gLinks
      .selectAll('path')
      .data(simLinks)
      .join('path')
      .attr('fill', 'none')
      .attr('stroke', (d) =>
        d.connectedToSelected ? 'rgba(0,233,123,0.9)' : 'rgba(255,255,255,0.25)'
      )
      .attr('stroke-width', (d) => (d.connectedToSelected ? 4 : 2))
      .attr('marker-end', (d) =>
        d.connectedToSelected ? 'url(#d3-arrow-highlight)' : 'url(#d3-arrow)'
      )
      .attr('opacity', 0)
      .attr('class', (d) => (d.connectedToSelected ? 'link-highlight' : ''));

    const nodeCircles = gNodes
      .selectAll('circle')
      .data(simNodes)
      .join('circle')
      .attr('r', (d) => {
        if (d.score == null) return nodeRadiusBase;
        const t = (d.score - minScore) / scoreRange;
        return nodeRadiusBase + t * (nodeRadiusMax - nodeRadiusBase);
      })
      .attr('opacity', 0)
      .attr('cx', (d) => d.x)
      .attr('cy', (d) => d.y)
      .attr('fill', (d) => d.fillColor ?? SCORE_COLOR_MAP[d.color] ?? '#22c55e')
      .attr('stroke', (d) => {
        if (selectedId && d.id === selectedId) return 'rgba(255,255,255,0.95)';
        if (ringHighlight && d.ring) return 'rgba(255,255,255,0.7)';
        if (d.ring) return 'rgba(255,255,255,0.4)';
        return 'none';
      })
      .attr('stroke-width', (d) => (selectedId && d.id === selectedId ? 3.5 : 2))
      .attr('filter', (d) => (selectedId && d.id === selectedId ? 'url(#d3-glow)' : 'none'))
      .style('cursor', 'pointer')
      .on('mouseenter', function (event, d) {
        hoverRef.current.setHoveredNode(d);
        hoverRef.current.setTooltipPos({
          x: (event as MouseEvent).clientX,
          y: (event as MouseEvent).clientY,
        });
        d3.select(this).raise().attr('stroke', 'white').attr('stroke-width', 2.5);
      })
      .on('mouseleave', function (_, d) {
        hoverRef.current.setHoveredNode(null);
        const isSuspicious = !!d.ring;
        d3.select(this)
          .attr(
            'stroke',
            isSuspicious && ringHighlight ? 'rgba(255,255,255,0.5)' : d.ring ? 'rgba(255,255,255,0.35)' : 'none'
          )
          .attr('stroke-width', 2);
      })
      .on('click', (_, d) => {
        const sel = selectedNodeRef.current?.id === d.id ? null : d;
        onSelectRef.current(sel);
      });

    function updateLinkPath(link: {
      source: { x: number; y: number };
      target: { x: number; y: number };
    }) {
      const sx = link.source.x;
      const sy = link.source.y;
      const tx = link.target.x;
      const ty = link.target.y;
      const dx = tx - sx;
      const dy = ty - sy;
      const len = Math.hypot(dx, dy) || 1;
      const u = dx / len;
      const v = dy / len;
      const dist = Math.min(len, nodeRadiusMax + 6);
      return lineGen([{ x: sx, y: sy }, { x: tx - u * dist, y: ty - v * dist }]);
    }

    const sim = d3
      .forceSimulation(simNodes as d3.SimulationNodeDatum[])
      .force(
        'link',
        d3.forceLink(simLinks).id((d) => (d as { id: string }).id).distance(70).strength(0.5)
      )
      .force('charge', d3.forceManyBody().strength(-180))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(nodeRadiusMax + 10))
      .on('tick', () => {
        linkPaths.attr('d', (d) => updateLinkPath(d));
        nodeCircles
          .attr('cx', (d: { x: number }) => d.x)
          .attr('cy', (d: { y: number }) => d.y)
          .attr('opacity', (d: { id: string }) =>
            selectedId && d.id !== selectedId ? 0.65 : 1
          );
        gRings.selectAll('polygon').remove();
        if (ringHighlight && fraudRings.length > 0) {
          const posMap = new Map(simNodes.map((n) => [n.id, { x: n.x, y: n.y }]));
          const ringColors = ['#0B5D3B', '#047857', '#065f46', '#134e4a', '#14532d'];
          fraudRings.forEach((ring, idx) => {
            const points = ring.member_accounts
              .map((id) => posMap.get(id))
              .filter((p): p is { x: number; y: number } => p != null);
            if (points.length < 3) return;
            const path = convexHull(points);
            if (!path) return;
            gRings
              .append('polygon')
              .attr('points', path)
              .attr('fill', 'none')
              .attr('stroke', ringColors[idx % ringColors.length])
              .attr('stroke-width', 3)
              .attr('stroke-dasharray', '10,8')
              .attr('stroke-linejoin', 'round')
              .attr('stroke-linecap', 'round')
              .attr('opacity', 0.95);
          });
        }
      });

    sim.alpha(0.9).restart();
    setTimeout(() => {
      linkPaths
        .transition()
        .duration(duration)
        .attr('opacity', (d: { connectedToSelected?: boolean }) =>
          d.connectedToSelected ? 1 : 0.7
        );
      nodeCircles
        .transition()
        .duration(duration)
        .attr('opacity', (d: { id: string }) =>
          selectedId && d.id !== selectedId ? 0.65 : 1
        );
    }, 100);

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 4])
      .on('start', () => svg.style('cursor', 'grabbing'))
      .on('end', () => svg.style('cursor', 'grab'))
      .on('zoom', (event) => {
        gZoom.attr('transform', event.transform);
      });
    svg.call(zoom);

    return () => {
      sim.stop();
      d3.select(el).selectAll('svg').remove();
    };
  }, [suspiciousOnly, ringHighlight, nodesProp, edgesProp, fraudRings, selectedNode]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const sel = d3.select(el).selectAll<SVGCircleElement, GraphNode>('.nodes circle');
    sel
      .attr('stroke', (d) => {
        const isSelected = selectedNode?.id === d.id;
        const isSuspicious = !!d.ring;
        if (isSelected) return 'white';
        return isSuspicious && ringHighlight ? 'rgba(255,255,255,0.5)' : 'none';
      })
      .attr('stroke-width', (d) => (selectedNode?.id === d.id ? 2.5 : 2));
  }, [selectedNode, ringHighlight]);

  return (
    <div ref={containerRef} className="relative w-full h-full overflow-hidden cursor-crosshair rounded-xl">
      {hoveredNode && (
        <div
          className="pointer-events-none fixed z-30 rounded-lg border border-white/20 bg-[#0f1419]/95 backdrop-blur px-3 py-2.5 shadow-xl text-left min-w-[180px]"
          style={{
            left: tooltipPos.x + 14,
            top: tooltipPos.y + 14,
          }}
        >
          <div className="text-[10px] font-bold uppercase tracking-wider text-white/50 mb-1.5">
            Node details
          </div>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between gap-4">
              <span className="text-white/50">User ID</span>
              <span className="font-medium text-white">{hoveredNode.id}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-white/50">Suspicion score</span>
              <span
                className="font-semibold"
                style={{ color: hoveredNode.fillColor ?? SCORE_COLOR_MAP[getScoreColorKey(hoveredNode.score)] }}
              >
                {hoveredNode.score != null ? hoveredNode.score.toFixed(1) : '–'}
              </span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-white/50">In transactions</span>
              <span className="text-white">{hoveredNode.inTx ?? '–'}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-white/50">Out transactions</span>
              <span className="text-white">{hoveredNode.outTx ?? '–'}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-white/50">Ring ID</span>
              <span className="text-[#00926B] font-medium">{hoveredNode.ring ?? '–'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
