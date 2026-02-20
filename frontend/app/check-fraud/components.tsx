'use client';

export function Toggle({
  on,
  onToggle,
  label,
}: {
  on: boolean;
  onToggle: () => void;
  label: string;
}) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm font-medium text-white/80">{label}</span>
      <button
        type="button"
        onClick={onToggle}
        className="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border border-white/10 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00926B] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0f1419] hover:opacity-90"
        style={{ background: on ? '#00926B' : 'rgba(255,255,255,0.08)' }}
        aria-pressed={on}
        aria-label={`${label}: ${on ? 'on' : 'off'}`}
      >
        <span
          className="pointer-events-none absolute top-0.5 left-0.5 inline-block h-5 w-5 rounded-full bg-white shadow-md transition-transform duration-200"
          style={{ transform: `translateX(${on ? 20 : 0}px)` }}
        />
      </button>
    </div>
  );
}

export function riskBadge(score: number): {
  bg: string;
  text: string;
  label: string;
} {
  if (score >= 85) return { bg: 'bg-red-500/20', text: 'text-red-400', label: score.toFixed(1) };
  if (score >= 60) return { bg: 'bg-amber-500/20', text: 'text-amber-400', label: score.toFixed(1) };
  return { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: score.toFixed(1) };
}
