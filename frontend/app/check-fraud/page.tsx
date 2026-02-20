'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
  Download,
  Upload,
  ArrowLeft,
  Search,
  Users,
  AlertTriangle,
  Wallet,
  Database,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { getResults, type ForensicResult } from '@/app/client/api';
import type { GraphNode } from './types';
import {
  nodesFromGraph,
  nodesFromResult,
  edgesFromGraph,
  ringsFromResult,
  getScoreRange,
  enrichNodesWithFillColor,
} from './graphUtils';
import { GraphCanvas } from './GraphCanvas';
import { Graph3D } from './Graph3D';
import { Toggle, riskBadge } from './components';
import {
  mockNodes,
  mockEdges,
  mockRings,
  jsonOutputPlaceholder,
} from './mockData';

const GAUGE_COLORS = ['#0d9488', '#f59e0b', '#f97316', '#ea580c', '#dc2626'] as const;

function SpeedometerGauge({
  min,
  max,
  value,
  label,
}: {
  min: number;
  max: number;
  value: number | null;
  label: string;
}) {
  const range = Math.max(max - min, 0.01);
  const angleMin = 135;
  const totalAngle = 180;
  const r = 44;
  const cx = 52;
  const cy = 52;
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const toXY = (angleDeg: number) => ({
    x: cx + r * Math.cos(toRad(angleDeg)),
    y: cy - r * Math.sin(toRad(angleDeg)),
  });
  const segments = 5;
  const pathSegments: { d: string; fill: string }[] = [];
  for (let i = 0; i < segments; i++) {
    const a0 = angleMin - (i / segments) * totalAngle;
    const a1 = angleMin - ((i + 1) / segments) * totalAngle;
    const p0 = toXY(a0);
    const p1 = toXY(a1);
    const d = `M ${cx} ${cy} L ${p0.x} ${p0.y} A ${r} ${r} 0 0 1 ${p1.x} ${p1.y} Z`;
    pathSegments.push({ d, fill: GAUGE_COLORS[i]! });
  }
  const valueAngle =
    value != null ? angleMin - ((value - min) / range) * totalAngle : null;
  const needleEnd = valueAngle != null ? toXY(valueAngle) : null;

  return (
    <div className="px-4 py-3 border-b border-white/10">
      <h3 className="text-[10px] font-bold uppercase tracking-widest text-white/40 mb-2">
        {label}
      </h3>
      <div className="flex flex-col items-center">
        <svg width={104} height={64} className="overflow-visible">
          <defs>
            <linearGradient id="gauge-bg" x1="0%" y1="0%" x2="100%" y2="0%">
              {GAUGE_COLORS.map((c, i) => (
                <stop key={c} offset={`${(i / (GAUGE_COLORS.length - 1)) * 100}%`} stopColor={c} />
              ))}
            </linearGradient>
          </defs>
          {pathSegments.map((seg, i) => (
            <path key={i} d={seg.d} fill={seg.fill} stroke="rgba(0,0,0,0.2)" strokeWidth={0.5} />
          ))}
          <circle cx={cx} cy={cy} r={28} fill="#0f1419" stroke="rgba(255,255,255,0.08)" strokeWidth={2} />
          {needleEnd && value != null && (
            <line
              x1={cx}
              y1={cy}
              x2={needleEnd.x}
              y2={needleEnd.y}
              stroke="rgba(255,255,255,0.9)"
              strokeWidth={2.5}
              strokeLinecap="round"
            />
          )}
          <text
            x={cx}
            y={cy + 4}
            textAnchor="middle"
            className="text-sm font-bold fill-white"
          >
            {value != null ? value.toFixed(1) : '–'}
          </text>
        </svg>
        <div className="flex justify-between w-full mt-1 px-1 text-[10px]">
          <span className="font-semibold text-[#0d9488]">{min.toFixed(1)}</span>
          <span className="text-white/50">min</span>
          <span className="text-white/50">max</span>
          <span className="font-semibold text-[#dc2626]">{max.toFixed(1)}</span>
        </div>
        <p className="text-[10px] text-white/40 mt-1.5 text-center">
          Larger node = higher score · Green lines = selected node edges
        </p>
      </div>
    </div>
  );
}

export default function FraudXAnalysis() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#020202] flex items-center justify-center text-white/60">
          Loading…
        </div>
      }
    >
      <FraudXAnalysisInner />
    </Suspense>
  );
}

function FraudXAnalysisInner() {
  const searchParams = useSearchParams();
  const sessionToken = searchParams.get('session');
  const [apiResult, setApiResult] = useState<ForensicResult | null>(null);
  const [resultsError, setResultsError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [suspiciousOnly, setSuspiciousOnly] = useState(false);
  const [ringHighlight, setRingHighlight] = useState(true);
  const [graph3D, setGraph3D] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [jsonOpen, setJsonOpen] = useState(false);

  useEffect(() => {
    if (!sessionToken) return;
    let cancelled = false;
    getResults(sessionToken)
      .then((res) => {
        if (!cancelled) {
          setApiResult(res);
          setResultsError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setResultsError(err instanceof Error ? err.message : 'Failed to load results');
          setApiResult(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [sessionToken]);

  const resultsLoading = !!sessionToken && !apiResult && !resultsError;

  const displayNodes = apiResult
    ? apiResult.graph && apiResult.graph.nodes.length > 0
      ? nodesFromGraph(apiResult.graph, apiResult.suspicious_accounts)
      : nodesFromResult(apiResult.suspicious_accounts)
    : enrichNodesWithFillColor(mockNodes);
  const displayEdges =
    apiResult?.graph && apiResult.graph.edges.length > 0
      ? edgesFromGraph(apiResult.graph)
      : apiResult
        ? []
        : mockEdges;
  const displayRings = apiResult ? ringsFromResult(apiResult.fraud_rings) : mockRings;
  const summary = apiResult?.summary;
  const statsList = summary
    ? [
        {
          label: 'Unique Accounts',
          value: String(summary.total_accounts_analyzed),
          color: '#00926B',
          icon: Users,
        },
        {
          label: 'Frauds Flagged',
          value: String(summary.suspicious_accounts_flagged),
          color: '#ef4444',
          icon: AlertTriangle,
        },
        {
          label: 'Total Amount',
          value:
            summary.total_amount != null && summary.total_amount > 0
              ? summary.total_amount >= 1e5
                ? `₹${(summary.total_amount / 1e5).toFixed(1)}L`
                : `₹${summary.total_amount.toLocaleString()}`
              : '–',
          color: '#00926B',
          icon: Wallet,
        },
        {
          label: 'Total Rows',
          value: String(summary.total_rows ?? summary.total_accounts_analyzed),
          color: '#00926B',
          icon: Database,
        },
      ]
    : [
        { label: 'Unique Accounts', value: '180', color: '#00926B', icon: Users },
        { label: 'Frauds Flagged', value: '24', color: '#ef4444', icon: AlertTriangle },
        { label: 'Total Amount', value: '₹10.25L', color: '#00926B', icon: Wallet },
        { label: 'Total Rows', value: '10,000', color: '#00926B', icon: Database },
      ];

  const jsonToShow = apiResult
    ? JSON.stringify(
        {
          suspicious_accounts: apiResult.suspicious_accounts,
          fraud_rings: apiResult.fraud_rings,
          summary: apiResult.summary,
        },
        null,
        2
      )
    : jsonOutputPlaceholder;

  const handleDownloadJSON = () => {
    const blob = new Blob([jsonToShow], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'fraud_analysis.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const scoreGauge = selectedNode?.score ?? 0;
  const scoreColor =
    scoreGauge >= 85 ? '#ef4444' : scoreGauge >= 60 ? '#f97316' : '#10b981';
  const R = 28;
  const C = 2 * Math.PI * R;

  return (
    <div className="min-h-screen bg-[#020202] text-white font-(--font-subheading) antialiased">
      <header className="sticky top-0 z-20 border-b border-white/10 bg-[#020202]/95 backdrop-blur-md">
        <div className="flex items-center justify-between px-4 sm:px-6 lg:px-8 py-4">
          <Link
            href="/"
            className="flex items-center justify-center w-10 h-10 rounded-full bg-white/5 border border-white/10 text-white/80 hover:bg-white/10 hover:text-white transition-colors"
            aria-label="Back to home"
          >
            <ArrowLeft size={20} />
          </Link>
          <div className="flex items-center gap-2">
            <span className="font-(--font-heading) text-xl font-extrabold tracking-tight">
              Fraud
            </span>
            <span className="font-(--font-heading) text-xl font-extrabold text-[#00926B]">
              X
            </span>
            <span className="text-white/70 font-medium text-sm ml-1 hidden sm:inline">
              Analysis
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/"
              className="inline-flex items-center gap-2 bg-[#00926B] text-white px-4 py-2.5 rounded-lg text-sm font-semibold hover:bg-[#007a55] transition-colors"
            >
              <Upload size={16} /> <span className="hidden sm:inline">Upload CSV</span>
            </Link>
            <button
              type="button"
              onClick={handleDownloadJSON}
              className="inline-flex items-center gap-2 bg-white/5 border border-white/10 text-white px-4 py-2.5 rounded-lg text-sm font-semibold hover:bg-white/10 transition-colors"
            >
              <Download size={16} /> <span className="hidden sm:inline">Export JSON</span>
            </button>
          </div>
        </div>
      </header>

      {resultsError && (
        <div className="mx-4 sm:mx-6 lg:mx-8 mt-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {resultsError}
        </div>
      )}

      <section className="px-4 sm:px-6 lg:px-8 py-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          {statsList.map(({ label, value, color, icon: Icon }) => (
            <div
              key={label}
              className="rounded-xl p-4 sm:p-5 border border-white/10 bg-white/2 hover:bg-white/4 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium uppercase tracking-wider text-white/50">
                  {label}
                </span>
                <span className="text-white/20" style={{ color }}>
                  <Icon size={18} />
                </span>
              </div>
              <div className="text-2xl sm:text-3xl font-bold tracking-tight" style={{ color }}>
                {value}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="px-4 sm:px-6 lg:px-8 pb-5">
        <div className="grid gap-4 lg:grid-cols-[1fr_minmax(240px,280px)]">
          <div
            className="relative overflow-hidden rounded-2xl min-h-[420px] sm:min-h-[500px]"
            style={{
              background: 'linear-gradient(135deg, #0a0d12 0%, #0f1419 40%, #0d1520 100%)',
              boxShadow: '0 0 0 1px rgba(0,233,123,0.15), 0 20px 50px -15px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05)',
            }}
          >
            <div
              className="absolute inset-0 rounded-2xl opacity-30"
              style={{
                background: 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(0,233,123,0.08) 0%, transparent 50%)',
                pointerEvents: 'none',
              }}
            />
            <div className="relative px-4 py-3 border-b border-white/5 flex items-center justify-between flex-wrap gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-white/50">
                Transaction Graph
                {graph3D ? (
                  <span className="text-[#00e87b]/70 font-normal"> · 3D</span>
                ) : (
                  <span className="text-white/40 font-normal"> · 2D</span>
                )}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setGraph3D((v) => !v)}
                  className="text-[10px] font-medium px-2.5 py-1 rounded-md border border-white/10 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white transition-colors"
                >
                  {graph3D ? 'Switch to 2D' : 'Switch to 3D'}
                </button>
                <span className="text-xs text-white/40">
                  {graph3D ? 'Orbit · Zoom · Click' : 'Pan · Zoom · Click'}
                </span>
              </div>
            </div>
            <div className="relative h-[380px] sm:h-[460px]">
              {resultsLoading ? (
                <div className="flex h-full items-center justify-center text-white/50 text-sm">
                  Loading results…
                </div>
              ) : graph3D ? (
                <Graph3D
                  nodes={displayNodes}
                  edges={displayEdges}
                  fraudRings={apiResult?.fraud_rings ?? []}
                  selectedNode={selectedNode}
                  onSelect={setSelectedNode}
                  suspiciousOnly={suspiciousOnly}
                />
              ) : (
                <GraphCanvas
                  nodes={displayNodes}
                  edges={displayEdges}
                  fraudRings={apiResult?.fraud_rings ?? []}
                  selectedNode={selectedNode}
                  onSelect={setSelectedNode}
                  suspiciousOnly={suspiciousOnly}
                  ringHighlight={ringHighlight}
                />
              )}
            </div>
          </div>

          <aside className="rounded-xl border border-white/10 bg-white/2 flex flex-col overflow-hidden">
            <div className="p-3 border-b border-white/10">
              <div className="flex items-center gap-2 rounded-lg bg-white/5 border border-white/10 px-3 py-2">
                <Search size={16} className="text-white/40 shrink-0" />
                <input
                  type="search"
                  placeholder="Search account..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 min-w-0 bg-transparent text-sm text-white placeholder-white/40 outline-none"
                  aria-label="Search account"
                />
              </div>
            </div>
            <div className="px-4 py-2 border-b border-white/10 space-y-0">
              <Toggle
                label="Suspicious only"
                on={suspiciousOnly}
                onToggle={() => setSuspiciousOnly((p) => !p)}
              />
              <Toggle
                label="Ring highlight"
                on={ringHighlight}
                onToggle={() => setRingHighlight((p) => !p)}
              />
            </div>
            <SpeedometerGauge
              min={getScoreRange(displayNodes).min}
              max={getScoreRange(displayNodes).max}
              value={selectedNode?.score ?? null}
              label="Score range (speedometer)"
            />
            <div className="px-4 py-4 border-b border-white/10">
              <h3 className="text-[10px] font-bold uppercase tracking-widest text-white/40 mb-3">
                Risk score
              </h3>
              <div className="flex items-center gap-4">
                <div className="relative shrink-0" style={{ width: 56, height: 56 }}>
                  <svg width="56" height="56" className="-rotate-90">
                    <circle
                      cx="28"
                      cy="28"
                      r={R}
                      fill="none"
                      stroke="rgba(255,255,255,0.08)"
                      strokeWidth="5"
                    />
                    <circle
                      cx="28"
                      cy="28"
                      r={R}
                      fill="none"
                      stroke={scoreColor}
                      strokeWidth="5"
                      strokeDasharray={`${(scoreGauge / 100) * C} ${C}`}
                      strokeLinecap="round"
                      className="transition-[stroke-dasharray] duration-300"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-sm font-bold" style={{ color: scoreColor }}>
                      {scoreGauge > 0 ? scoreGauge : '–'}
                    </span>
                  </div>
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-white truncate">
                    {selectedNode ? selectedNode.id : 'No account selected'}
                  </p>
                  <p className="text-xs text-white/50">
                    {selectedNode ? 'Risk level' : 'Click a node to inspect'}
                  </p>
                  {selectedNode && (
                    <p className="text-xs font-bold mt-0.5" style={{ color: scoreColor }}>
                      {scoreGauge >= 85
                        ? 'High risk'
                        : scoreGauge >= 60
                          ? 'Medium risk'
                          : 'Low risk'}
                    </p>
                  )}
                </div>
              </div>
            </div>
            <div className="px-4 py-4 border-b border-white/10">
              <h3 className="text-[10px] font-bold uppercase tracking-widest text-white/40 mb-2">
                Detected patterns
              </h3>
              {selectedNode && apiResult ? (
                (() => {
                  const acc = apiResult.suspicious_accounts.find(
                    (a) => a.account_id === selectedNode.id
                  );
                  const patterns = acc?.detected_patterns ?? [];
                  return patterns.length ? (
                    <div className="flex flex-wrap gap-1.5">
                      {patterns.map((p) => (
                        <span
                          key={p}
                          className="text-xs font-mono px-2 py-1 rounded-md bg-white/5 text-white/80 border border-white/10"
                        >
                          {p}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-white/40">No patterns</p>
                  );
                })()
              ) : selectedNode?.ring ? (
                <div className="flex flex-wrap gap-1.5">
                  {['cycle_detected', 'fan_out', 'high_velocity'].slice(0, 3).map((p) => (
                    <span
                      key={p}
                      className="text-xs font-mono px-2 py-1 rounded-md bg-white/5 text-white/80 border border-white/10"
                    >
                      {p}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-white/40">Select a suspicious node</p>
              )}
            </div>
            <div className="px-4 py-4 flex-1 overflow-auto">
              <h3 className="text-[10px] font-bold uppercase tracking-widest text-white/40 mb-3">
                Account details
              </h3>
              <dl className="space-y-2">
                {[
                  ['Account ID', selectedNode ? selectedNode.id : '–'],
                  ['In transactions', selectedNode?.inTx ?? '–'],
                  ['Out transactions', selectedNode?.outTx ?? '–'],
                  [
                    'Total amount',
                    selectedNode?.totalAmount
                      ? `₹${selectedNode.totalAmount.toLocaleString()}`
                      : '–',
                  ],
                  ['Active days', selectedNode?.activeDays ?? '–'],
                  [
                    'Active txn amount',
                    selectedNode?.activeTxAmount
                      ? `₹${selectedNode.activeTxAmount.toLocaleString()}`
                      : '–',
                  ],
                ].map(([k, v]) => (
                  <div
                    key={String(k)}
                    className="flex justify-between items-center gap-2 text-xs"
                  >
                    <dt className="text-white/50">{k}</dt>
                    <dd className="font-medium text-white truncate max-w-[55%]">
                      {String(v)}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </aside>
        </div>
      </section>

      <section className="px-4 sm:px-6 lg:px-8 pb-5">
        <div className="rounded-xl border border-white/10 bg-white/2 overflow-hidden">
          <div className="px-4 sm:px-5 py-3 border-b border-white/10">
            <h2 className="text-sm font-semibold text-white">Detected fraud rings</h2>
            <p className="text-xs text-white/50 mt-0.5">Rings and pattern types from analysis</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10 bg-white/3">
                  {['Ring ID', 'Pattern type', 'Members', 'Risk score', 'Accounts'].map((h) => (
                    <th
                      key={h}
                      className="text-left px-4 sm:px-5 py-3 text-[10px] font-bold uppercase tracking-wider text-white/50"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {displayRings.map((ring) => {
                  const badge = riskBadge(ring.riskScore);
                  return (
                    <tr
                      key={ring.ringId}
                      className="border-b border-white/5 hover:bg-white/3 transition-colors"
                    >
                      <td className="px-4 sm:px-5 py-3 font-semibold text-[#00926B]">
                        {ring.ringId}
                      </td>
                      <td className="px-4 sm:px-5 py-3 text-white/90">{ring.patternType}</td>
                      <td className="px-4 sm:px-5 py-3 text-white/80">{ring.members}</td>
                      <td className="px-4 sm:px-5 py-3">
                        <span
                          className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-bold ${badge.bg} ${badge.text}`}
                        >
                          {badge.label}
                        </span>
                      </td>
                      <td
                        className="px-4 sm:px-5 py-3 text-white/70 font-mono text-xs truncate max-w-[180px]"
                        title={ring.accounts}
                      >
                        {ring.accounts}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="px-4 sm:px-6 lg:px-8 pb-10">
        <div className="rounded-xl border border-white/10 bg-white/2 overflow-hidden">
          <button
            type="button"
            onClick={() => setJsonOpen((o) => !o)}
            className="w-full flex items-center justify-between px-4 sm:px-5 py-3 border-b border-white/10 hover:bg-white/3 transition-colors text-left"
          >
            <span className="text-sm font-semibold text-white">JSON output</span>
            <span className="text-white/50">
              {jsonOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </span>
          </button>
          {jsonOpen && (
            <div className="p-4">
              <div className="flex justify-end mb-2">
                <button
                  type="button"
                  onClick={handleDownloadJSON}
                  className="inline-flex items-center gap-2 bg-[#00926B] text-white px-3 py-1.5 rounded-lg text-xs font-semibold hover:bg-[#007a55] transition-colors"
                >
                  <Download size={14} /> Export
                </button>
              </div>
              <pre className="p-4 rounded-lg bg-[#0d1117] text-xs leading-relaxed overflow-x-auto font-mono border border-white/10">
                {jsonToShow.split('\n').map((line, i) => {
                  const colored = line
                    .replace(/"([^"]+)":/g, (_m, k) => `<span style="color:#7dd3fc">"${k}":</span>`)
                    .replace(/: "([^"]+)"/g, (_m, v) => `: <span style="color:#fde68a">"${v}"</span>`)
                    .replace(/: (\d+\.?\d*)/g, (_m, v) => `: <span style="color:#f97316">${v}</span>`);
                  return (
                    <div
                      key={i}
                      dangerouslySetInnerHTML={{ __html: colored || ' ' }}
                      style={{ color: 'rgba(255,255,255,0.6)' }}
                    />
                  );
                })}
              </pre>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
