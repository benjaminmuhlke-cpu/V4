export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center text-center px-8">
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1600&q=80')`,
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-earth-dark/70 via-earth-dark/40 to-earth-dark/85" />

      <div className="relative z-10 flex flex-col items-center gap-6">
        <img
          src="/logo.svg"
          alt="楞先生"
          className="w-64 md:w-80 drop-shadow-2xl"
          style={{ filter: 'drop-shadow(0 6px 24px rgba(0,0,0,0.6))' }}
        />
        <p className="text-earth-stone tracking-[0.25em] uppercase text-sm md:text-base font-display italic">
          Outdoor &amp; Technical Clothing
        </p>
        <p className="text-earth-tan tracking-[0.15em] text-xs md:text-sm uppercase">
          From Head to Toe — Tested for Every Condition
        </p>
      </div>

      <div className="absolute bottom-10 flex flex-col items-center gap-2 text-earth-stone">
        <span className="text-xs tracking-[0.2em] uppercase">Discover</span>
        <div className="w-px h-10 bg-gradient-to-b from-earth-tan to-transparent" />
      </div>
    </section>
  );
}
