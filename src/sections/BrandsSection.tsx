const brands = [
  { name: 'Ecco',          domain: 'ecco.com' },
  { name: 'Aigle',         domain: 'aigle.com' },
  { name: 'Smartwool',     domain: 'smartwool.com' },
  { name: 'Montbell',      domain: 'montbell.com' },
  { name: 'Lafuma',        domain: 'lafuma.com' },
  { name: 'Marmot',        domain: 'marmot.com' },
  { name: 'Icebreaker',    domain: 'icebreaker.com' },
  { name: 'TBS',           domain: 'tbs.fr' },
  { name: 'Prana',         domain: 'prana.com' },
  { name: 'GoLite',        domain: 'golite.com' },
  { name: 'Fusalp',        domain: 'fusalp.com' },
  { name: 'Cloudveil',     domain: 'cloudveil.com' },
  { name: 'Gregory',       domain: 'gregorypacks.com' },
  { name: 'Coleman',       domain: 'coleman.com' },
  { name: 'Gore-Tex',      domain: 'gore-tex.com' },
  { name: 'Wigwam',        domain: 'wigwam.com' },
  { name: 'Keen',          domain: 'keenfootwear.com' },
  { name: 'Stanley',       domain: 'stanley1913.com' },
  { name: 'Nalgene',       domain: 'nalgene.com' },
  { name: 'Ziener',        domain: 'ziener.com' },
  { name: 'Buff',          domain: 'buffusa.com' },
  { name: 'Black Diamond', domain: 'blackdiamondequipment.com' },
  { name: 'CamelBak',      domain: 'camelbak.com' },
  { name: 'Chaco',         domain: 'chacousa.com' },
  { name: 'Oofos',         domain: 'oofos.com' },
];

export default function BrandsSection() {
  return (
    <section className="bg-cream px-8 py-24">
      <div className="text-center mb-16">
        <p className="text-earth-amber text-xs tracking-[0.3em] uppercase mb-3">我們的品牌</p>
        <h2 className="font-display text-4xl md:text-5xl text-earth-brown">精選品牌</h2>
      </div>

      <div
        className="max-w-5xl mx-auto grid border border-earth-stone"
        style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(155px, 1fr))' }}
      >
        {brands.map(({ name, domain }) => (
          <div
            key={name}
            className="group border border-earth-stone px-4 py-6 flex flex-col items-center justify-center gap-3 transition-colors duration-200 hover:bg-forest cursor-default"
          >
            <img
              src={`https://logo.clearbit.com/${domain}`}
              alt={name}
              className="h-10 w-auto max-w-[100px] object-contain group-hover:brightness-0 group-hover:invert transition-all duration-200"
              onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
            />
            <span className="font-display font-bold text-sm text-earth-brown group-hover:text-cream transition-colors duration-200 text-center">
              {name}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
