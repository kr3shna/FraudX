import type { GraphData } from '@/app/client/api';
import type { SuspiciousAccount, FraudRing } from '@/app/client/api';
import type { GraphNode, GraphEdge, RingRow, ScoreColorKey } from './types';
import { getScoreColorKey, getScoreColorHex } from './scoreUtils';
import { circleLayout } from './scoreUtils';

export { getScoreColorKey, getScoreColorHex, circleLayout };

/** Min/max scores among nodes (for legend). */
export function getScoreRange(nodes: GraphNode[]): { min: number; max: number } {
  const scores = nodes.map((n) => n.score).filter((s): s is number => s != null);
  if (scores.length === 0) return { min: 0, max: 100 };
  return { min: Math.min(...scores), max: Math.max(...scores) };
}

/** Add fillColor to nodes with scores (for mock data). */
export function enrichNodesWithFillColor(nodes: GraphNode[]): GraphNode[] {
  const { min, max } = getScoreRange(nodes);
  return nodes.map((n) => ({
    ...n,
    fillColor:
      n.score != null ? getScoreColorHex(n.score, min, max) : undefined,
  }));
}

/** Compute min/max scores among accounts with scores. */
function scoreRange(accounts: SuspiciousAccount[]): { min: number; max: number } {
  const scores = accounts.map((a) => a.suspicion_score).filter((s) => s != null);
  if (scores.length === 0) return { min: 0, max: 100 };
  return { min: Math.min(...scores), max: Math.max(...scores) };
}

/** Build nodes from API graph + suspicious_accounts. Color by dynamic min-max range. */
export function nodesFromGraph(graph: GraphData, accounts: SuspiciousAccount[]): GraphNode[] {
  const accMap = new Map(accounts.map((a) => [a.account_id, a]));
  const gnMap = new Map(graph.nodes.map((gn) => [gn.id, gn]));
  const { min: minScore, max: maxScore } = scoreRange(accounts);
  const allIds = [...new Set([...graph.nodes.map((gn) => gn.id), ...accounts.map((a) => a.account_id)])];
  const positions = circleLayout(allIds.length);
  return allIds.map((id, i) => {
    const gn = gnMap.get(id);
    const acc = accMap.get(id);
    const score = acc?.suspicion_score;
    const color = getScoreColorKey(score);
    const fillColor = score != null ? getScoreColorHex(score, minScore, maxScore) : undefined;
    return {
      id,
      x: positions[i].x,
      y: positions[i].y,
      color,
      fillColor,
      ring: acc?.ring_id === 'NONE' ? undefined : acc?.ring_id,
      score: score ?? undefined,
      inTx: gn?.in_degree ?? 0,
      outTx: gn?.out_degree ?? 0,
      totalAmount: gn?.total_transactions ?? 0,
    };
  });
}

/** Build graph nodes from API suspicious_accounts only (no graph). Color by dynamic min-max range. */
export function nodesFromResult(accounts: SuspiciousAccount[]): GraphNode[] {
  const n = accounts.length;
  const { min: minScore, max: maxScore } = scoreRange(accounts);
  const positions = circleLayout(n);
  return accounts.map((a, i) => {
    const score = a.suspicion_score;
    const color = getScoreColorKey(score);
    const fillColor = getScoreColorHex(score, minScore, maxScore);
    return {
      id: a.account_id,
      x: positions[i].x,
      y: positions[i].y,
      color,
      fillColor,
      ring: a.ring_id === 'NONE' ? undefined : a.ring_id,
      score,
    };
  });
}

/** Build edges from API graph (directed: source -> target). */
export function edgesFromGraph(graph: GraphData): GraphEdge[] {
  return graph.edges.map((e) => ({ from: e.source, to: e.target }));
}

/** Map API fraud_rings to table Ring shape. */
export function ringsFromResult(fraudRings: FraudRing[]): RingRow[] {
  return fraudRings.map((r) => ({
    ringId: r.ring_id,
    patternType: r.pattern_type,
    members: r.member_accounts.length,
    riskScore: r.risk_score,
    accounts: r.member_accounts.join(', '),
  }));
}

/** Convex hull of points for ring boundary (returns polygon points string). */
export function convexHull(points: { x: number; y: number }[]): string {
  if (points.length < 3) return '';
  const sorted = [...points].sort((a, b) => a.x - b.x || a.y - b.y);
  const cross = (
    o: { x: number; y: number },
    a: { x: number; y: number },
    b: { x: number; y: number }
  ) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  const lower: { x: number; y: number }[] = [];
  for (const p of sorted) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0)
      lower.pop();
    lower.push(p);
  }
  const upper: { x: number; y: number }[] = [];
  for (let i = sorted.length - 1; i >= 0; i--) {
    const p = sorted[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0)
      upper.pop();
    upper.push(p);
  }
  lower.pop();
  upper.pop();
  const hull = [...lower, ...upper];
  return hull.length > 0 ? hull.map((p) => `${p.x},${p.y}`).join(' ') : '';
}
