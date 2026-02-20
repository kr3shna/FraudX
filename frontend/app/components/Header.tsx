import Image from 'next/image';

export default function Header() {
  return (
    <header className="relative z-10 bg-transparent px-4 py-6 md:py-8">
      {/* Centered dark capsule nav */}
      <nav className="flex justify-center">
        <div className="inline-flex items-center gap-6 md:gap-8 px-6 md:px-8 py-3 md:py-3.5 rounded-full bg-[#020202]/80 border border-white/10 shadow-xl backdrop-blur-sm">
          <a
            href="#pipeline"
            className="flex items-center"
          >
            <Image
              src="/logo.png"
              alt="GraphTrail logo"
              width={96}
              height={28}
              className="h-7 w-auto rounded-sm object-contain"
            />
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
          <a
            href="#upload-csv"
            className="bg-[#00926B] text-white px-5 py-2.5 rounded-full font-medium hover:bg-[#007a55] transition-colors text-sm ml-2 inline-block"
          >
            Upload CSV
          </a>
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
