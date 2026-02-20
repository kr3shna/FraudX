'use client';
import Image from 'next/image';
import { Skull } from 'lucide-react';

const CycleIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
    <polyline points="21 3 21 9 15 9"/>
  </svg>
);

const ShellIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <circle cx="12" cy="12" r="4"/>
    <line x1="4.93" y1="4.93" x2="9.17" y2="9.17"/>
    <line x1="14.83" y1="14.83" x2="19.07" y2="19.07"/>
    <line x1="14.83" y1="9.17" x2="19.07" y2="4.93"/>
    <line x1="4.93" y1="19.07" x2="9.17" y2="14.83"/>
  </svg>
);

const SmurfIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="3" y1="6" x2="21" y2="6"/>
    <line x1="3" y1="12" x2="21" y2="12"/>
    <line x1="3" y1="18" x2="21" y2="18"/>
  </svg>
);

function PatternCard({ icon, category, title, description, visual, algorithm }: {
  icon: React.ReactNode;
  category: string;
  title: string;
  description: string;
  visual: React.ReactNode;
  algorithm: string;
}) {
  return (
    <div className="bg-[#0f0f14] border border-white/[0.08] rounded-xl p-5 backdrop-blur-sm">
      {/* Visual box */}
      <div className="bg-white/[0.04] border border-white/10 rounded-lg px-4 py-3 mb-2.5 font-mono text-sm text-[#e84040] tracking-wide">
        {visual}
      </div>

      {/* Algorithm box */}
      <div className="bg-white border border-white/[0.07] rounded-lg px-4 py-2.5 mb-5">
        <div className="text-[9px] font-mono text-gray-500 font-bold tracking-[2px] uppercase mb-1">
          ALGORITHM
        </div>
        <div className="text-[13px] text-black font-weight-500 font-mono">
          {algorithm}
        </div>
      </div>

      {/* Badge */}
      <div className="inline-flex items-center gap-1.5 bg-white/[0.06] border border-white/10 rounded-full px-3 py-1 mb-3 text-white/60 text-xs">
        {icon}
        {category}
      </div>

      {/* Title */}
      <div className="text-[15px] font-bold text-white mb-2 tracking-tight">
        {title}
      </div>

      {/* Description */}
      <div className="text-[13px] text-white/45 leading-relaxed font-sans">
        {description}
      </div>
    </div>
  );
}

export default function ThreeWays() {
  const leftPatterns = [
    {
      icon: <CycleIcon />,
      category: "Cycle Detection",
      title: "Circular Fund Routing",
      description: "Money loops through multiple accounts and returns near its origin, severing the traceable trail. Classic layering used by organized mule rings.",
      visual: "A → B → C → A",
      algorithm: "Johnson's Cycle Detection · Depth 3–5",
    },
    {
      icon: <ShellIcon />,
      category: "Shell Networks",
      title: "Layered Shell Accounts",
      description: "Funds pass through ghost intermediary accounts with minimal transaction history, adding complexity to obscure the true destination.",
      visual: <span className="flex items-center gap-1.5">ORIGIN → <Skull size={14} /> → <Skull size={14} /> → <Skull size={14} /> → DEST</span>,
      algorithm: "BFS Chain Traversal · ≤3 txn/node",
    },
  ];

  const rightPattern = {
    icon: <SmurfIcon />,
    category: "Smurfing",
    title: "Fan-In / Fan-Out",
    description: "Dozens of small deposits aggregate into one hub account, then instantly disperse — deliberately staying below reporting thresholds.",
    visual: "10+ → HUB → 10+ | 72hr window",
    algorithm: "In/Out-Degree Analysis · Temporal BFS",
  };

  return (
    <div className="min-h-screen bg-#020202 text-white font-serif relative overflow-hidden">

      {/* Bottom-right 3D circle image */}
      <div className="absolute right-[-40px] bottom-0 w-[520px] h-[580px] z-0 opacity-90 pointer-events-none">
        <Image
          src="/3D Circle 1.png"
          alt=""
          fill
          className="object-contain object-bottom"
          sizes="(max-width: 768px) 45vw, 520px"
          priority={false}
        />
      </div>

      {/* Top-right teal glow */}
      <div
        className="absolute top-[-80px] right-[60px] w-[300px] h-[200px] pointer-events-none blur-[40px]"
        style={{ background: "radial-gradient(ellipse, rgba(0,180,120,0.12) 0%, transparent 70%)" }}
      />

      {/* Content */}
      <div className="relative z-10">

        {/* Header */}
        <div className="text-center pt-12 pb-10">
          <div className="flex items-center justify-center gap-2.5 mb-5">
            <div className="w-6 h-px bg-white/40" />
            <span className="text-[11px] tracking-[3px] text-white/45 uppercase font-mono">
              DETECTION PATTERNS
            </span>
            <div className="w-6 h-px bg-white/40" />
          </div>

          <h1 className="m-0 text-[clamp(36px,6vw,64px)] font-bold leading-[1.15] tracking-[-1.5px] font-serif">
            Three Ways Mules<br />
            Move{" "}
            <span className="text-[#00926B]">Dirty Money</span>
          </h1>
        </div>

        {/* Cards grid */}
        <div className="grid grid-cols-2 gap-15 max-w-[900px] mx-auto px-8 pb-16">

          {/* Left column: 2 stacked */}
          <div className="flex flex-col gap-5">
            {leftPatterns.map((pattern, i) => (
              <PatternCard key={i} {...pattern} />
            ))}
          </div>

          {/* Right column: 1 tall card */}
          <div className="bg-[#0f0f14] border border-white/[0.08] rounded-xl max-h-[350px] mt-40  p-5 backdrop-blur-sm flex flex-col box-border">
            {/* Visual box */}
            <div className="bg-white/[0.04] border border-white/10 rounded-lg px-4 py-3 mb-2.5 font-mono text-sm text-[#e84040] tracking-wide">
              {rightPattern.visual}
            </div>

            {/* Algorithm box */}
            <div className="bg-white border border-white/[0.07] rounded-lg px-4 py-2.5 mb-5">
              <div className="text-[9px] font-mono text-gray-500 font-bold tracking-[2px] uppercase mb-1">
                ALGORITHM
              </div>
              <div className="text-[13px] text-black font-weight-500 font-mono">
                {rightPattern.algorithm}
              </div>
            </div>

            {/* Badge */}
            <div className="inline-flex items-center gap-1.5 bg-white/[0.06] border border-white/10 rounded-full px-3 py-1 mb-3 text-white/60 text-xs w-fit">
              <SmurfIcon />
              {rightPattern.category}
            </div>

            {/* Title */}
            <div className="text-[15px] font-bold text-white mb-2 tracking-tight">
              {rightPattern.title}
            </div>

            {/* Description */}
            <div className="text-[13px] text-white/45 leading-relaxed font-sans">
              {rightPattern.description}
            </div>

            <div className="flex-1" />
          </div>

        </div>
      </div>
    </div>
  );
}
