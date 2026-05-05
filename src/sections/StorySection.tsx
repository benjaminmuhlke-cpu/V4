const stats = [
  { number: '25+', label: 'Years of Experience' },
  { number: '25+', label: 'Curated Brands' },
  { number: '100%', label: 'Tested & Approved' },
];

export default function StorySection() {
  return (
    <section className="bg-earth-dark px-8 py-24">
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-16 items-start">
        <div className="flex flex-col gap-10">
          {stats.map(({ number, label }) => (
            <div key={label}>
              <div className="font-display text-5xl font-black text-earth-amber leading-none">
                {number}
              </div>
              <div className="text-earth-stone text-xs tracking-[0.2em] uppercase mt-2">
                {label}
              </div>
            </div>
          ))}
        </div>

        <div className="md:col-span-2">
          <p className="text-earth-amber text-xs tracking-[0.3em] uppercase mb-3">Our Story</p>
          <h2 className="font-display text-4xl md:text-5xl text-cream mb-8 leading-tight">
            Passion for the Outdoors,<br />Since Day One
          </h2>
          <p className="text-earth-stone text-lg leading-relaxed mb-5">
            楞先生 is a <strong className="text-cream font-semibold">family-owned outdoor store</strong> built
            by passionate people who live and breathe the outdoors. For over 25 years, we have been equipping
            adventurers — from weekend hikers to seasoned mountaineers — with gear they truly need.
          </p>
          <p className="text-earth-stone text-lg leading-relaxed mb-5">
            Every brand on our shelves has been{' '}
            <strong className="text-cream font-semibold">personally tested and approved</strong> across all
            weather and conditions. We don't sell what we wouldn't wear ourselves.
          </p>
          <p className="text-earth-stone text-lg leading-relaxed">
            Come to us with a challenge — whether it's sub-zero peaks, monsoon trails, or multi-week
            expeditions — and <strong className="text-cream font-semibold">we will find exactly what you need</strong>,
            from head to toe.
          </p>
        </div>
      </div>
    </section>
  );
}
