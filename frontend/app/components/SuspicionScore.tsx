'use client';

import { useState } from 'react';

// ── Types ─────────────────────────────────────────────────────────
interface Pattern {
  id: number;
  name: string;
  points: number;
  active: boolean;
  icon: string;
  activeColor: 'teal' | 'red' | 'yellow' | 'gray';
}

// ── Icons ─────────────────────────────────────────────────────────
const CycleIcon = ({ color }: { color: string }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);
const FanIcon = ({ color }: { color: string }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
  </svg>
);
const BoltIcon = ({ color }: { color: string }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);
const BoxIcon = ({ color }: { color: string }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
  </svg>
);
const OverlapIcon = ({ color }: { color: string }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
  </svg>
);

function getPatternIcon(iconType: string, active: boolean, activeColor: string) {
  const onColor =
    activeColor === 'teal' ? '#0d9488' :
    activeColor === 'red' ? '#ef4444' :
    activeColor === 'yellow' ? '#eab308' : '#9ca3af';
  const offColor = '#6b7280';
  const color = active ? onColor : offColor;

  switch (iconType) {
    case 'cycle': return <CycleIcon color={color} />;
    case 'fan': return <FanIcon color={color} />;
    case 'velocity': return <BoltIcon color={color} />;
    case 'shell': return <BoxIcon color={color} />;
    case 'overlap': return <OverlapIcon color={color} />;
    default: return null;
  }
}

// ── Toggle Switch ─────────────────────────────────────────────────
function Toggle({ active, onToggle, color }: { active: boolean; onToggle: () => void; color: string }) {
  const trackColor =
    !active ? 'rgba(255,255,255,0.15)' :
    color === 'teal' ? '#0d9488' :
    color === 'red' ? '#ef4444' : '#eab308';

  return (
    <button
      onClick={onToggle}
      style={{
        position: 'relative',
        width: '44px',
        height: '24px',
        borderRadius: '12px',
        background: trackColor,
        border: 'none',
        cursor: 'pointer',
        transition: 'background 0.25s',
        flexShrink: 0,
      }}
    >
      <span style={{
        position: 'absolute',
        top: '3px',
        left: active ? '23px' : '3px',
        width: '18px',
        height: '18px',
        borderRadius: '50%',
        background: '#ffffff',
        transition: 'left 0.25s',
        boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
      }} />
    </button>
  );
}

// ── Pattern Row ───────────────────────────────────────────────────
function PatternRow({ pattern, onToggle }: { pattern: Pattern; onToggle: () => void }) {
  const rowBg =
    pattern.active && pattern.activeColor === 'teal' ? 'rgba(204,251,241,0.92)' :
    pattern.active && pattern.activeColor === 'red' ? 'rgba(254,226,226,0.92)' :
    'rgba(20,22,30,0.9)';

  const namColor =
    pattern.active && pattern.activeColor === 'teal' ? '#134e4a' :
    pattern.active && pattern.activeColor === 'red' ? '#7f1d1d' :
    'rgba(255,255,255,0.88)';

  const ptsColor =
    pattern.active && pattern.activeColor === 'teal' ? '#0f766e' :
    pattern.active && pattern.activeColor === 'red' ? '#b91c1c' :
    'rgba(255,255,255,0.38)';

  const borderColor =
    pattern.active && pattern.activeColor === 'teal' ? 'rgba(94,234,212,0.5)' :
    pattern.active && pattern.activeColor === 'red' ? 'rgba(252,165,165,0.5)' :
    'rgba(255,255,255,0.07)';

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '13px 16px',
      borderRadius: '10px',
      background: rowBg,
      border: `1px solid ${borderColor}`,
      transition: 'background 0.25s, border-color 0.25s',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 }}>
        {/* Icon circle */}
        <div style={{
          width: '34px',
          height: '34px',
          borderRadius: '50%',
          background: 'rgba(0,0,0,0.12)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          {getPatternIcon(pattern.icon, pattern.active, pattern.activeColor)}
        </div>

        <div>
          <div style={{ fontSize: '14px', fontWeight: '600', color: namColor, lineHeight: '1.3' }}>
            {pattern.name}
          </div>
          <div style={{ fontSize: '12px', color: ptsColor, marginTop: '1px' }}>
            +{pattern.points} points
          </div>
        </div>
      </div>

      <Toggle active={pattern.active} onToggle={onToggle} color={pattern.activeColor} />
    </div>
  );
}

// ── Circular Score Gauge ──────────────────────────────────────────
function ScoreGauge({ score }: { score: number }) {
  const R = 80;
  const C = 2 * Math.PI * R;
  const progress = Math.min(score / 100, 1);
  const dash = progress * C;
  const gap = C - dash;

  const riskLabel =
    score >= 75 ? 'HIGH RISK' :
    score >= 40 ? 'MEDIUM RISK' : 'LOW RISK';

  const riskColor =
    score >= 75 ? '#ef4444' :
    score >= 40 ? '#f97316' : '#22c55e';

  return (
    <div style={{ position: 'relative', width: '192px', height: '192px' }}>
      <svg
        width="192" height="192"
        style={{ transform: 'rotate(-90deg)', display: 'block' }}
      >
        {/* Track */}
        <circle
          cx="96" cy="96" r={R}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="14"
        />
        {/* Progress */}
        <circle
          cx="96" cy="96" r={R}
          fill="none"
          stroke="#0d9488"
          strokeWidth="14"
          strokeDasharray={`${dash} ${gap}`}
          strokeLinecap="round"
        />
      </svg>
      {/* Center label */}
      <div style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '4px',
      }}>
        <span style={{
          fontSize: '52px',
          fontWeight: '800',
          color: '#ffffff',
          lineHeight: 1,
          fontFamily: "var(--font-heading), Georgia, serif",
        }}>{score}</span>
        <span style={{
          fontSize: '11px',
          fontWeight: '700',
          letterSpacing: '1.5px',
          color: riskColor,
          textTransform: 'uppercase',
        }}>{riskLabel}</span>
      </div>
    </div>
  );
}

// ── Score Bar ─────────────────────────────────────────────────────
function ScoreBar({
  label, value, barColor, textColor,
}: { label: string; value: number; barColor: string; textColor: string }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ fontSize: '14px', color: 'rgba(255,255,255,0.75)', fontWeight: '500' }}>{label}</span>
        <span style={{ fontSize: '18px', fontWeight: '800', color: value > 0 ? textColor : '#f97316', fontFamily: "var(--font-heading), Georgia, serif" }}>
          {value}
        </span>
      </div>
      {/* Bar track */}
      <div style={{
        width: '100%',
        height: '6px',
        borderRadius: '3px',
        background: 'rgba(255,255,255,0.1)',
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%',
          borderRadius: '3px',
          background: barColor,
          width: `${value}%`,
          transition: 'width 0.4s ease',
        }} />
      </div>
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────
export default function SuspicionScore() {
  const [patterns, setPatterns] = useState<Pattern[]>([
    { id: 1, name: 'Cycle Detected (length 3)', points: 40, active: true,  icon: 'cycle',    activeColor: 'teal' },
    { id: 2, name: 'Fan-Out Hub (12 receivers)', points: 25, active: true,  icon: 'fan',      activeColor: 'red'  },
    { id: 3, name: 'High Velocity (72hr window)', points: 20, active: false, icon: 'velocity', activeColor: 'yellow'},
    { id: 4, name: 'Shell Chain (3 hops)',         points: 30, active: false, icon: 'shell',    activeColor: 'gray' },
    { id: 5, name: 'Multi-Pattern Overlap Bonus',  points: 10, active: false, icon: 'overlap',  activeColor: 'gray' },
  ]);

  const toggle = (id: number) =>
    setPatterns(prev => prev.map(p => p.id === id ? { ...p, active: !p.active } : p));

  const totalScore  = patterns.filter(p => p.active).reduce((s, p) => s + p.points, 0);
  const cycleW      = patterns[0].active ? patterns[0].points : 0;
  const smurfingW   = patterns[1].active ? patterns[1].points : 0;
  const velocityW   = patterns[2].active ? patterns[2].points : 0;
  const shellW      = patterns[3].active ? patterns[3].points : 0;

  const activeTags  = patterns.filter(p => p.active).map(p =>
    p.icon === 'cycle' ? 'cycle_length_3' :
    p.icon === 'fan'   ? 'fan_out' :
    p.icon === 'velocity' ? 'high_velocity' :
    p.icon === 'shell' ? 'shell_chain' : 'multi_pattern'
  );

  // shared card style
  const card = {
    background: 'rgba(12,14,20,0.92)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '16px',
    backdropFilter: 'blur(14px)',
    boxShadow: '0 4px 40px rgba(0,0,0,0.5)',
  } as const;

  return (
    <section style={{
      background: '#020202',
      color: '#fff',
      padding: '72px 40px',
      minHeight: '100vh',
      fontFamily: "var(--font-subheading), 'Segoe UI', sans-serif",
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Ambient glow bottom-right */}
      <div style={{
        position: 'absolute', right: '-60px', bottom: '-60px',
        width: '380px', height: '380px',
        background: 'radial-gradient(ellipse, rgba(0,200,80,0.18) 0%, transparent 70%)',
        filter: 'blur(60px)', pointerEvents: 'none',
      }} />

      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '28px', alignItems: 'start' }}>

          {/* ═══════════════ LEFT COLUMN ═══════════════ */}
          <div>
            {/* Title section — no card */}
            <div style={{ marginBottom: '32px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
                <div style={{ width: '28px', height: '1.5px', background: 'rgba(255,255,255,0.5)' }} />
                <span style={{ fontSize: '10px', letterSpacing: '3px', color: 'rgba(255,255,255,0.55)', textTransform: 'uppercase' }}>
                  SCORE ENGINE
                </span>
              </div>

              <h2 style={{
                margin: '0 0 16px',
                fontSize: 'clamp(32px, 4vw, 48px)',
                fontWeight: '800',
                lineHeight: '1.1',
                letterSpacing: '-1.5px',
                fontFamily: "var(--font-heading), Georgia, serif",
              }}>
                See How Suspicion<br />
                Score <span style={{ color: '#00926B' }}>Works</span>
              </h2>

              <p style={{ margin: 0, fontSize: '14px', color: 'rgba(255,255,255,0.5)', lineHeight: '1.7', maxWidth: '460px' }}>
                Toggle each detected pattern to see how it contributes to the final risk score in real time.
              </p>
            </div>

            {/* Patterns card */}
            <div style={{ ...card, padding: '20px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {patterns.map(p => (
                  <PatternRow key={p.id} pattern={p} onToggle={() => toggle(p.id)} />
                ))}
              </div>
            </div>
          </div>

          {/* ═══════════════ RIGHT COLUMN ═══════════════ */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

            {/* ── Live Score card ── */}
            <div style={{ ...card, padding: '32px 28px' }}>
              <div style={{
                fontSize: '10px', letterSpacing: '3px',
                color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: '28px',
              }}>
                LIVE SUSPICION SCORE
              </div>

              {/* Gauge */}
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '22px' }}>
                <ScoreGauge score={totalScore} />
              </div>

              {/* Account ID */}
              <div style={{
                textAlign: 'center',
                fontSize: '14px',
                fontWeight: '500',
                color: 'rgba(255,255,255,0.75)',
                letterSpacing: '0.5px',
                marginBottom: '16px',
              }}>
                ACC_00347 · RING_001
              </div>

              {/* Tags */}
              <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', flexWrap: 'wrap' }}>
                {activeTags.length === 0 ? (
                  <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.3)' }}>No patterns active</span>
                ) : activeTags.map(tag => (
                  <span key={tag} style={{
                    padding: '4px 14px',
                    borderRadius: '20px',
                    border: '1px solid rgba(255,255,255,0.25)',
                    fontSize: '11.5px',
                    color: 'rgba(255,255,255,0.75)',
                    fontFamily: 'monospace',
                    letterSpacing: '0.3px',
                  }}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* ── Score Breakdown card ── */}
            <div style={{ ...card, padding: '28px' }}>
              <div style={{
                fontSize: '10px', letterSpacing: '3px',
                color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', marginBottom: '24px',
              }}>
                SCORE BREAKDOWN
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <ScoreBar label="Cycle Weight"    value={cycleW}    barColor="#0d9488" textColor="#0d9488" />
                <ScoreBar label="Smurfing Weight" value={smurfingW} barColor="#ef4444" textColor="#ef4444" />
                <ScoreBar label="Velocity Weight" value={velocityW} barColor="#eab308" textColor="#eab308" />
                <ScoreBar label="Shell Weight"    value={shellW}    barColor="#9ca3af" textColor="#9ca3af" />
              </div>
            </div>

          </div>
        </div>
      </div>
    </section>
  );
}
