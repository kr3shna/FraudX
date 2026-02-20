import type { ScoreColorKey } from './types';

/** Fixed-band coloring (legacy). */
export function getScoreColorKey(score: number | undefined): ScoreColorKey {
  if (score == null || score < 12) return 'normal';
  if (score >= 85) return 'critical';
  if (score >= 70) return 'high';
  if (score >= 55) return 'medium_high';
  if (score >= 40) return 'medium';
  return 'low';
}

/** 5-color scale within [minScore, maxScore]. Returns hex for fraud nodes. */
const FRAUD_COLOR_SCALE = ['#0d9488', '#f59e0b', '#f97316', '#ea580c', '#dc2626'] as const;

export function getScoreColorHex(
  score: number,
  minScore: number,
  maxScore: number
): string {
  const range = Math.max(maxScore - minScore, 0.001);
  const t = (score - minScore) / range;
  const idx = Math.min(Math.floor(t * 5), 4);
  return FRAUD_COLOR_SCALE[idx]!;
}

export function circleLayout(n: number): { x: number; y: number }[] {
  const centerX = 400;
  const centerY = 270;
  const radius = Math.min(220, 80 + n * 4);
  return Array.from({ length: n }, (_, i) => ({
    x: centerX + radius * Math.cos((i / Math.max(n, 1)) * 2 * Math.PI - Math.PI / 2),
    y: centerY + radius * Math.sin((i / Math.max(n, 1)) * 2 * Math.PI - Math.PI / 2),
  }));
}
