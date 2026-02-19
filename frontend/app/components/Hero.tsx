'use client';

import Image from 'next/image';

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-start justify-center overflow-hidden">

      {/* Wave image — full section background */}
      <div className="absolute inset-0 z-0">
        <Image
          src="/wave-bg.png"
          alt=""
          fill
          className="object-cover object-center"
          sizes="100vw"
          priority
        />
        {/* Dark overlay so text is readable on top */}
        <div className="absolute inset-0 bg-black/30" />
      </div>

      {/* Content — sits on top of wave */}
      <div className="relative z-10 max-w-4xl mx-auto text-center px-6 pt-24 pb-16">

        {/* Main title */}
        <h1 className="text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-bold text-white leading-tight tracking-tight font-serif mb-6">
          Expose the{' '}
          <span className="text-[#00926B]">Money Mule</span>{' '}
          Networks{' '}
          <span className="text-[#00926B]">Rings</span>
        </h1>

        {/* Description */}
        <p className="text-base md:text-lg text-white/80 max-w-2xl mx-auto mb-10 leading-relaxed">
          A graph-based forensics engine that uncovers illicit fund flows through
          multi-hop account networks — detecting cycles, smurfing, and layered
          shells that traditional systems miss entirely.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button className="bg-[#00926B] text-white px-8 py-3 rounded-full font-semibold hover:bg-[#007a55] transition-colors">
            Upload CSV
          </button>
          <a
            href="#pipeline"
            className="text-white/80 hover:text-white transition-colors font-medium flex items-center gap-1.5"
          >
            See how its work <span>→</span>
          </a>
        </div>
      </div>
    </section>
  );
}