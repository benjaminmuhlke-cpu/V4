const collaborators = [
  'Epoch Hospitality',
  'Soleil Collective',
  'Noire Atelier',
  'Harbour & Co',
  'Forma Collective',
  'Aura Interiors',
  'Vela Studio',
  'Meridian Group',
];

// Duplicate for seamless loop
const items = [...collaborators, ...collaborators];

export default function CollaboratorsBanner() {
  return (
    <div className="border-y border-white/10 bg-ink overflow-hidden py-5">
      <div className="mb-3 px-6 md:px-10 lg:px-16">
        <span className="text-[0.6rem] font-medium uppercase tracking-[0.3em] text-white/30">
          Selected Collaborators
        </span>
      </div>
      <div className="relative flex overflow-hidden">
        <div
          className="flex shrink-0 gap-16"
          style={{ animation: 'marquee 30s linear infinite' }}
        >
          {items.map((name, i) => (
            <span
              key={i}
              className="whitespace-nowrap text-xs font-medium uppercase tracking-[0.25em] text-accent"
            >
              {name}
              <span className="ml-8 text-accent">·</span>
            </span>
          ))}
        </div>
      </div>
      <style>{`
        @keyframes marquee {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
