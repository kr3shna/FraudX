'use client';

// ── Types ─────────────────────────────────────────────────────────
interface Ring {
  patternType: string;
  members: number;
  riskScore: number;
  accounts: string;
}

// ── Data ──────────────────────────────────────────────────────────
const rings: Ring[] = [
  {
    patternType: 'Cycle + Smurfing',
    members: 5,
    riskScore: 95.3,
    accounts: 'ACC_001, ACC_002, ACC_003, ACC_004, ACC_005',
  },
  {
    patternType: 'Shell Network',
    members: 4,
    riskScore: 72.1,
    accounts: 'ACC_010, ACC_011, ACC_012, ACC_013',
  },
  {
    patternType: 'Fan-Out (Smurfing)',
    members: 12,
    riskScore: 61.4,
    accounts: 'ACC_020, ACC_021, ... +10 more',
  },
];

const jsonLines: { text: string; color: string }[][] = [
  [{ text: '{', color: 'rgba(255,255,255,0.5)' }],
  [
    { text: '  "suspicious_accounts": [', color: '#7dd3fc' },
  ],
  [{ text: '    {', color: 'rgba(255,255,255,0.5)' }],
  [
    { text: '      "account_id": ', color: '#7dd3fc' },
    { text: '"ACC_00123"', color: '#fde68a' },
    { text: ',', color: 'rgba(255,255,255,0.4)' },
  ],
  [
    { text: '      "suspicion_score": ', color: '#7dd3fc' },
    { text: '87.5', color: '#f97316' },
    { text: ',', color: 'rgba(255,255,255,0.4)' },
  ],
  [
    { text: '      "detected_patterns": [', color: '#7dd3fc' },
    { text: '"cycle_length_3", "high_velocity"', color: '#fde68a' },
    { text: '],', color: 'rgba(255,255,255,0.4)' },
  ],
  [
    { text: '      "ring_id": ', color: '#7dd3fc' },
    { text: '"RING_001"', color: '#fde68a' },
  ],
  [{ text: '    }', color: 'rgba(255,255,255,0.5)' }],
  [{ text: '  ],', color: 'rgba(255,255,255,0.4)' }],
  [{ text: '  "fraud_rings": [...],', color: '#7dd3fc' }],
  [{ text: '  "summary": {', color: '#7dd3fc' }],
  [
    { text: '    "total_accounts_analyzed": ', color: '#7dd3fc' },
    { text: '500', color: '#f97316' },
    { text: ',', color: 'rgba(255,255,255,0.4)' },
  ],
  [
    { text: '    "suspicious_accounts_flagged": ', color: '#7dd3fc' },
    { text: '15', color: '#f97316' },
    { text: ',', color: 'rgba(255,255,255,0.4)' },
  ],
  [
    { text: '    "fraud_rings_detected": ', color: '#7dd3fc' },
    { text: '4', color: '#f97316' },
    { text: ',', color: 'rgba(255,255,255,0.4)' },
  ],
  [
    { text: '    "processing_time_seconds": ', color: '#7dd3fc' },
    { text: '2.3', color: '#f97316' },
  ],
  [{ text: '  }', color: 'rgba(255,255,255,0.5)' }],
  [{ text: '}', color: 'rgba(255,255,255,0.5)' }],
];

// ── Risk badge colour ─────────────────────────────────────────────
function riskBadgeStyle(score: number): { background: string; color: string } {
  if (score >= 90) return { background: 'rgba(239,68,68,0.25)', color: '#f87171' };
  if (score >= 65) return { background: 'rgba(234,179,8,0.22)', color: '#facc15' };
  return { background: 'rgba(20,184,166,0.22)', color: '#2dd4bf' };
}

// ── Icon box ──────────────────────────────────────────────────────
function IconBox({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      width: '40px', height: '40px', borderRadius: '10px',
      background: 'rgba(255,255,255,0.08)',
      border: '1px solid rgba(255,255,255,0.1)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
    }}>
      {children}
    </div>
  );
}

// ── Star icon (graph) ─────────────────────────────────────────────
const StarIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
    stroke="rgba(255,255,255,0.55)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
  </svg>
);

// ── Download icon ─────────────────────────────────────────────────
const DownloadIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
    stroke="rgba(255,255,255,0.55)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
  </svg>
);

// ── Bar chart icon ────────────────────────────────────────────────
const BarIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
    stroke="rgba(255,255,255,0.55)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

// ── Check icon ────────────────────────────────────────────────────
const CheckIcon = () => (
  <svg width="14" height="14" viewBox="0 0 20 20" fill="#10b981" style={{ flexShrink: 0, marginTop: '2px' }}>
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
  </svg>
);

// ── Shared card style ─────────────────────────────────────────────
const card: React.CSSProperties = {
  background: 'rgba(10,12,20,0.88)',
  border: '1px solid rgba(255,255,255,0.09)',
  borderRadius: '16px',
  backdropFilter: 'blur(14px)',
  boxShadow: '0 4px 40px rgba(0,0,0,0.45)',
  overflow: 'hidden',
};

// ── Main Component ────────────────────────────────────────────────
export default function ForensicResults() {
  return (
    <section style={{
      background: '#020202',
      color: '#fff',
      padding: '64px 40px 80px',
      fontFamily: "'Inter', 'Helvetica Neue', sans-serif",
      position: 'relative',
      overflow: 'hidden',
      minHeight: '100vh',
    }}>
      {/* ambient green glow – left */}
      <div style={{
        position: 'absolute', left: '-100px', top: '38%',
        width: '420px', height: '420px', zIndex: 0,
        background: 'radial-gradient(ellipse, rgba(0,200,80,0.28) 0%, rgba(0,140,50,0.14) 40%, transparent 70%)',
        filter: 'blur(60px)', pointerEvents: 'none',
        transform: 'translateY(-50%)',
      }} />

      <div style={{ maxWidth: '1240px', margin: '0 auto', position: 'relative', zIndex: 1 }}>

        {/* ── Header ── */}
        <div style={{ marginBottom: '48px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
            <div style={{ width: '28px', height: '1.5px', background: '#10b981' }} />
            <span style={{ fontSize: '10px', letterSpacing: '3.5px', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase' }}>
              REQUIRED OUTPUTS
            </span>
          </div>
          <h2 style={{
            margin: 0,
            fontSize: 'clamp(40px, 5vw, 60px)',
            fontWeight: '800',
            lineHeight: '1.1',
            letterSpacing: '-2px',
            fontFamily: "'Georgia', 'Times New Roman', serif",
          }}>
            Forensic-Grade<br />
            <span style={{ color: '#00926B' }}>Results</span>
          </h2>
        </div>

        {/* ── Top two cards ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>

          {/* Left — Interactive Graph */}
          <div style={{ ...card }}>
            {/* Card header row */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: '14px',
              padding: '22px 24px',
              borderBottom: '1px solid rgba(255,255,255,0.07)',
            }}>
              <IconBox><StarIcon /></IconBox>
              <div>
                <div style={{ fontSize: '15px', fontWeight: '700', color: '#fff', marginBottom: '3px' }}>
                  Interactive Graph Visualization
                </div>
                <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.45)' }}>
                  Click nodes to inspect · Filter by ring · Zoom & pan
                </div>
              </div>
            </div>

            {/* Body */}
            <div style={{ padding: '28px 24px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '36px' }}>
                {[
                  'All sender & receiver accounts as directed nodes',
                  'Fraud rings highlighted in distinct colors',
                  'Hover tooltip with full account metadata & score',
                  'Suspicious nodes visually distinct (larger, red border)',
                ].map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                    <CheckIcon />
                    <span style={{ fontSize: '13.5px', color: 'rgba(255,255,255,0.75)', lineHeight: '1.5' }}>{f}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right — JSON Report */}
          <div style={{ ...card }}>
            {/* Card header row */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: '14px',
              padding: '22px 24px',
              borderBottom: '1px solid rgba(255,255,255,0.07)',
            }}>
              <IconBox><DownloadIcon /></IconBox>
              <div>
                <div style={{ fontSize: '15px', fontWeight: '700', color: '#fff', marginBottom: '3px' }}>
                  Downloadable JSON Report
                </div>
                <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.45)' }}>
                  Exact format matching required for evaluation
                </div>
              </div>
            </div>

            {/* Code block */}
            <div style={{ padding: '20px 24px 24px' }}>
              <div style={{
                background: 'rgba(8,10,22,0.95)',
                borderRadius: '10px',
                padding: '20px 22px',
                border: '1px solid rgba(255,255,255,0.06)',
                overflowX: 'auto',
              }}>
                <pre style={{ margin: 0, fontFamily: "'Fira Code', 'Courier New', monospace", fontSize: '12px', lineHeight: '1.8' }}>
                  {jsonLines.map((line, li) => (
                    <div key={li}>
                      {line.map((seg, si) => (
                        <span key={si} style={{ color: seg.color }}>{seg.text}</span>
                      ))}
                    </div>
                  ))}
                </pre>
              </div>
            </div>
          </div>
        </div>

        {/* ── Bottom — Fraud Ring Table ── */}
        <div style={{ ...card }}>
          {/* Card header */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: '14px',
            padding: '22px 28px',
            borderBottom: '1px solid rgba(255,255,255,0.07)',
          }}>
            <IconBox><BarIcon /></IconBox>
            <div>
              <div style={{ fontSize: '15px', fontWeight: '700', color: '#fff', marginBottom: '3px' }}>
                Fraud Ring Summary Table
              </div>
              <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.45)' }}>
                Every detected ring with full member details
              </div>
            </div>
          </div>

          {/* Table */}
          <div style={{ padding: '8px 28px 32px', overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.12)' }}>
                  {['PATTERN TYPE', 'MEMBERS', 'RISK SCORE', 'MEMBER ACCOUNTS'].map((h) => (
                    <th key={h} style={{
                      padding: '14px 16px',
                      textAlign: 'left',
                      fontSize: '10.5px',
                      fontWeight: '700',
                      letterSpacing: '1.5px',
                      color: 'rgba(255,255,255,0.5)',
                      textTransform: 'uppercase',
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rings.map((ring, idx) => {
                  const badge = riskBadgeStyle(ring.riskScore);
                  return (
                    <tr key={idx} style={{
                      borderBottom: idx < rings.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none',
                    }}>
                      {/* Pattern type */}
                      <td style={{ padding: '18px 16px', fontSize: '13.5px', color: 'rgba(255,255,255,0.82)' }}>
                        {ring.patternType}
                      </td>
                      {/* Members */}
                      <td style={{ padding: '18px 16px', fontSize: '13.5px', color: 'rgba(255,255,255,0.82)' }}>
                        {ring.members}
                      </td>
                      {/* Risk score badge */}
                      <td style={{ padding: '18px 16px' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: '3px 12px',
                          borderRadius: '6px',
                          fontSize: '13px',
                          fontWeight: '700',
                          background: badge.background,
                          color: badge.color,
                          fontFamily: 'monospace',
                          letterSpacing: '0.3px',
                        }}>
                          {ring.riskScore}
                        </span>
                      </td>
                      {/* Accounts */}
                      <td style={{ padding: '18px 16px', fontSize: '13px', color: 'rgba(255,255,255,0.6)', fontFamily: 'monospace' }}>
                        {ring.accounts}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* dotted bottom rule */}
            <div style={{ marginTop: '24px', borderTop: '2px dashed rgba(255,255,255,0.1)' }} />
          </div>
        </div>

      </div>
    </section>
  );
}