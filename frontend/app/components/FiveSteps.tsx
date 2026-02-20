"use client";

import React from "react";

type Step = {
  id: number;
  icon: React.ReactNode;
  iconBg: string;
  badge: string;
  description: string;
};

// ── Icon Components ──────────────────────────────────────────────
const FolderIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
    stroke="#334155" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
  </svg>
);

const GraphIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
    stroke="#334155" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
);

const CodeIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
    stroke="#2563eb" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16 18 22 12 16 6" />
    <polyline points="8 6 2 12 8 18" />
  </svg>
);

const AlertIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
    stroke="#ef4444" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
);

const ExportIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
    stroke="#6366f1" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
);

// ── Step Data ────────────────────────────────────────────────────
const steps: Step[] = [
  {
    id: 1,
    icon: <FolderIcon />,
    iconBg: "linear-gradient(135deg, #d1d5db, #e5e7eb)",
    badge: "CSV Ingestion",
    description:
      "Upload your transactions. PapaParse streams rows and validates all 5 required columns instantly.",
  },
  {
    id: 2,
    icon: <GraphIcon />,
    iconBg: "linear-gradient(135deg, #cbd5e1, #e2e8f0)",
    badge: "Graph Build",
    description:
      "Network constructs a directed weighted graph — accounts as nodes, transactions as edges.",
  },
  {
    id: 3,
    icon: <CodeIcon />,
    iconBg: "linear-gradient(135deg, #bfdbfe, #dbeafe)",
    badge: "Algorithm Suite",
    description:
      "Cycle detection, degree analysis, BFS traversal and temporal windowing run in parallel.tly.",
  },
  {
    id: 4,
    icon: <AlertIcon />,
    iconBg: "linear-gradient(135deg, #fecaca, #fee2e2)",
    badge: "Suspicion Score",
    description:
      "Each account receives a 0–100 weighted risk score based on pattern hits and velocity.",
  },
  {
    id: 5,
    icon: <ExportIcon />,
    iconBg: "linear-gradient(135deg, #ddd6fe, #ede9fe)",
    badge: "Visualize & Export",
    description:
      "Interactive graph renders flagged rings. Download the full forensics JSON report.",
  },
];

// ── Step Card ────────────────────────────────────────────────────
// Wrapper handles the top overflow space so the icon doesn't get clipped
function StepCard({ icon, iconBg, badge, description }: Omit<Step, "id">) {
  return (
    // Outer wrapper: provides padding-top space for the floating icon circle
    <div style={{ position: "relative", paddingTop: "28px" }}>

      {/* Floating circle icon — sits above the card border */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: "-10px",
          width: "52px",
          height: "52px",
          background: iconBg,
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 4px 18px rgba(0,0,0,0.45)",
          border: "2px solid rgba(255,255,255,0.12)",
          zIndex: 2,
        }}
      >
        {icon}
      </div>

      {/* Card body */}
      <div
        style={{
          background: "rgba(10,12,20,0.84)",
          border: "1px solid rgba(255,255,255,0.09)",
          borderRadius: "10px",
          padding: "32px 22px 26px",
          backdropFilter: "blur(12px)",
          boxShadow: "0 4px 40px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04)",
          minHeight: "165px",
        }}
      >
        {/* Badge pill */}
        <div
          style={{
            display: "inline-block",
            background: "rgba(35,40,54,0.98)",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "20px",
            padding: "4px 14px",
            fontSize: "12.5px",
            fontWeight: "600",
            color: "rgba(255,255,255,0.88)",
            marginBottom: "14px",
            letterSpacing: "0.1px",
            fontFamily: "var(--font-subheading), 'Segoe UI', sans-serif",
          }}
        >
          {badge}
        </div>

        {/* Description */}
        <p
          style={{
            margin: 0,
            fontSize: "13.5px",
            color: "rgba(255,255,255,0.52)",
            lineHeight: "1.72",
            fontFamily: "var(--font-subheading), 'Segoe UI', sans-serif",
          }}
        >
          {description}
        </p>
      </div>
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────
export default function FollowTheMoney() {
  return (
    <section
      style={{
        minHeight: "100vh",
        background: "#020202",
        color: "#fff",
        position: "relative",
        overflow: "hidden",
        padding: "0 0 90px",
      }}
    >
      {/* ── Green ambient blob — left ── */}
      <div
        style={{
          position: "absolute",
          left: "-90px",
          top: "50%",
          width: "440px",
          height: "440px",
          background:
            "radial-gradient(ellipse, rgba(0,200,80,0.3) 0%, rgba(0,140,50,0.16) 38%, transparent 70%)",
          filter: "blur(58px)",
          pointerEvents: "none",
          transform: "translateY(-40%)",
          zIndex: 0,
        }}
      />

      {/* ── Subtle top-right glow ── */}
      <div
        style={{
          position: "absolute",
          right: "-40px",
          top: "8%",
          width: "260px",
          height: "200px",
          background:
            "radial-gradient(ellipse, rgba(0,80,160,0.1) 0%, transparent 70%)",
          filter: "blur(52px)",
          pointerEvents: "none",
          zIndex: 0,
        }}
      />

      {/* ── Page Content ── */}
      <div style={{ position: "relative", zIndex: 1 }}>

        {/* Header */}
        <div style={{ textAlign: "center", paddingTop: "60px", paddingBottom: "56px" }}>
          {/* PIPELINE label */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "10px",
              marginBottom: "26px",
            }}
          >
            <div style={{ width: "28px", height: "1.5px", background: "rgba(255,255,255,0.35)" }} />
            <span
              style={{
                fontSize: "10px",
                letterSpacing: "4px",
                color: "rgba(255,255,255,0.4)",
                textTransform: "uppercase",
                fontFamily: "monospace",
              }}
            >
              PIPELINE
            </span>
          </div>

          {/* Title */}
          <h2
            style={{
              margin: 0,
              fontSize: "clamp(40px, 6vw, 72px)",
              fontWeight: "800",
              lineHeight: "1.1",
              letterSpacing: "-2.5px",
              fontFamily: "var(--font-heading), Georgia, serif",
            }}
          >
            Follow The Money
            <br />
            In{" "}
            <span style={{ color: "#00926B" }}>5 Steps</span>
          </h2>
        </div>

        {/* ── Cards container ── */}
        <div
          style={{
            maxWidth: "1080px",
            margin: "0 auto",
            padding: "0 36px",
          }}
        >
          {/* ── Row 1: 3 cards ── */}
          <div
            style={{
              display: "flex",
              gap: "40px",
              marginBottom: "20px",
              overflow: "visible",
            }}
          >
            {steps.slice(0, 3).map((step) => (
              <div key={step.id} style={{ flex: "1 1 0" }}>
                <StepCard {...step} />
              </div>
            ))}
          </div>

          {/* ── Row 2: 2 cards — centered under cols 2 & 3 ── */}
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              gap: "20px",
              overflow: "visible",
            }}
          >
            {steps.slice(3).map((step) => (
              <div key={step.id} style={{ flex: "0 0 calc(33.333% - 10px)" }}>
                <StepCard {...step} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
