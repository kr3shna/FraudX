'use client';

export default function Footer() {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="relative z-10 bg-[#020202] border-t border-white/10 text-white px-6 py-12 md:px-12">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          {/* Left Section */}
          <div>
            <div className="text-2xl font-bold text-[#00926B] mb-2">
              GraphSentinel
            </div>
            <div className="text-sm text-white/80 mb-1">
              Graph-Based Financial Crime Detection Engine
            </div>
            <div className="text-xs text-white/60">
              Built for RIFT 2026 Hackathon - Graph Theory Track
            </div>
          </div>

          {/* Move to top */}
          <button
            type="button"
            onClick={scrollToTop}
            className="w-12 h-12 rounded-full bg-[#00926B] text-white font-semibold hover:bg-[#007a55] transition-colors flex items-center justify-center shrink-0"
            aria-label="Scroll to top"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M12 19V5M5 12l7-7 7 7" />
            </svg>
          </button>
        </div>
      </div>
    </footer>
  );
}