export default function LogoCircle({ className = '' }: { className?: string }) {
  return (
    <div
      className={`w-10 h-10 rounded-full bg-white/10 border border-white/30 flex items-center justify-center shrink-0 backdrop-blur-sm ${className}`}
      aria-hidden
    >
      <span className="text-white text-xl font-medium leading-none" style={{ fontFamily: 'system-ui, sans-serif' }}>
        ₹
      </span>
    </div>
  );
}
