export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center text-center px-8">
      <div
        className="absolute inset-0"
        style={{
          background: `
            radial-gradient(ellipse at 20% 50%, #2C4A2E 0%, transparent 55%),
            radial-gradient(ellipse at 80% 20%, #4A3728 0%, transparent 50%),
            radial-gradient(ellipse at 60% 80%, #1C1208 0%, transparent 60%),
            linear-gradient(160deg, #1C1208 0%, #2C4A2E 40%, #4A3728 70%, #1C1208 100%)
          `,
        }}
      />
      <div className="absolute inset-0" style={{ background: 'rgba(28,18,8,0.35)' }} />

      <div className="relative z-10 flex flex-col items-center gap-6">
        <img
          src="/logo.svg"
          alt="楞先生"
          className="w-64 md:w-80 drop-shadow-2xl"
          style={{ filter: 'drop-shadow(0 6px 24px rgba(0,0,0,0.6))' }}
        />
        <p className="text-earth-stone tracking-[0.25em] uppercase text-sm md:text-base font-display italic">
          戶外機能服飾
        </p>
        <p className="text-earth-tan tracking-[0.15em] text-xs md:text-sm uppercase">
          從頭到腳，全天候嚴選裝備
        </p>
      </div>

      <div className="absolute bottom-10 flex flex-col items-center gap-2 text-earth-stone">
        <span className="text-xs tracking-[0.2em] uppercase">探索</span>
        <div className="w-px h-10 bg-gradient-to-b from-earth-tan to-transparent" />
      </div>
    </section>
  );
}
