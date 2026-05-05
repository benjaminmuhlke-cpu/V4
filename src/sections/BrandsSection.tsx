const brands = [
  'Ecco', 'Aigle', 'Smartwool', 'Montbell', 'Lafuma',
  'Marmot', 'Icebreaker', 'TBS', 'Prana', 'GoLite',
  'Fusalp', 'Cloudveil', 'Gregory', 'Coleman', 'Gore-Tex',
  'Wigwam', 'Keen', 'Stanley', 'Nalgene', 'Ziener',
  'Buff', 'Black Diamond', 'CamelBak', 'Chaco', 'Oofos',
];

export default function BrandsSection() {
  return (
    <section className="bg-cream px-8 py-24">
      <div className="text-center mb-16">
        <p className="text-earth-amber text-xs tracking-[0.3em] uppercase mb-3">What We Carry</p>
        <h2 className="font-display text-4xl md:text-5xl text-earth-brown">Our Brands</h2>
      </div>

      <div
        className="max-w-5xl mx-auto grid border border-earth-stone"
        style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(155px, 1fr))' }}
      >
        {brands.map((brand) => (
          <div
            key={brand}
            className="group border border-earth-stone px-4 py-7 text-center transition-colors duration-200 hover:bg-forest cursor-default"
          >
            <span className="font-display font-bold text-sm text-earth-brown group-hover:text-cream transition-colors duration-200">
              {brand}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
