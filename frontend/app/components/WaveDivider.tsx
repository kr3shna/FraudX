'use client';

import Image from 'next/image';

/**
 * Wave background: ~50px at bottom of Hero, ~50px at top of ThreeWays.
 * Parent must be position: relative.
 */
export default function WaveDivider() {
  return (
    <div
      className="absolute left-0 right-0 z-0 overflow-hidden pointer-events-none"
      style={{
        top: 'calc(100% - 50px)',
        height: 'min(60vh, 500px)',
        minHeight: '320px',
      }}
    >
      <div className="relative w-full h-full">
        <Image
          src="/wave-bg.png"
          alt=""
          fill
          className="object-cover object-center"
          sizes="100vw"
          priority
        />
      </div>
    </div>
  );
}
