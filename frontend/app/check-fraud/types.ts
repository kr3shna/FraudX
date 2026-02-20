/** Score-based color band for fraud nodes; 'normal' = non-fraud (green). */
export type ScoreColorKey = 'normal' | 'low' | 'medium' | 'medium_high' | 'high' | 'critical';

export interface GraphNode {
  id: string;
  x: number;
  y: number;
  color: ScoreColorKey;
  /** Hex color from dynamic min-max score scale; used when present. */
  fillColor?: string;
  ring?: string;
  score?: number;
  inTx?: number;
  outTx?: number;
  totalAmount?: number;
  activeDays?: number;
  activeTxAmount?: number;
}

export interface GraphEdge {
  from: string;
  to: string;
}

/** Alias for graph node (avoids conflict with DOM Node). */
export type Node = GraphNode;
/** Alias for graph edge. */
export type Edge = GraphEdge;

export interface RingRow {
  ringId: string;
  patternType: string;
  members: number;
  riskScore: number;
  accounts: string;
}

/** At least 5 colors for fraud by score; rest = green (non-fraud). */
export const SCORE_COLOR_MAP: Record<ScoreColorKey, string> = {
  normal: '#22c55e',
  low: '#0d9488',
  medium: '#f59e0b',
  medium_high: '#f97316',
  high: '#ea580c',
  critical: '#dc2626',
};
