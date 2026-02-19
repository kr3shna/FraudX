export default function Header() {
  return (
    <header className="relative z-10 bg-transparent px-4 py-6 md:py-8">
      {/* Centered dark capsule nav */}
      <nav className="flex justify-center">
        <div className="inline-flex items-center gap-6 md:gap-8 px-6 md:px-8 py-3 md:py-3.5 rounded-full bg-[#020202]/80 border border-white/10 shadow-xl backdrop-blur-sm">
          <a
            href="#pipeline"
            className="text-white/90 hover:text-white transition-colors text-sm font-medium flex items-center gap-1.5"
          >
            <svg className="w-4 h-4 text-white/80" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            Pipeline
          </a>
          <a
            href="#score"
            className="text-white/90 hover:text-white transition-colors text-sm font-medium"
          >
            Score Engine
          </a>
          <a
            href="#faqs"
            className="text-white/90 hover:text-white transition-colors text-sm font-medium"
          >
            FAQs
          </a>
          <a
            href="#changelog"
            className="text-white/90 hover:text-white transition-colors text-sm font-medium"
          >
            Changelog
          </a>
          <button className="bg-[#00926B] text-white px-5 py-2.5 rounded-full font-medium hover:bg-[#007a55] transition-colors text-sm ml-2">
            Upload CSV
          </button>
        </div>
      </nav>

      {/* Mobile menu trigger - only show on small screens */}
      <div className="md:hidden absolute top-6 right-4">
        <button className="text-white/90 p-2" aria-label="Menu">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>
    </header>
  );
}
