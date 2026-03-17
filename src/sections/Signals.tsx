import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { InfiniteSlider } from '../components/ui/infinite-slider';
import { fadeUp, staggerContainer } from '../lib/motion';

const stats = [
  { value: '10', label: 'Years of Experience' },
  { value: '60', label: 'Projects' },
];

const collaborators = [
  { kind: 'wordmark', label: 'Maison Verite' },
  { kind: 'badge', label: 'OC', sublabel: 'Oblique Coffee' },
  { kind: 'wordmark', label: 'Forma Collective' },
  { kind: 'badge', label: 'AI', sublabel: 'Aura Interiors' },
  { kind: 'wordmark', label: 'Sable FW' },
  { kind: 'badge', label: 'MS', sublabel: 'Meridian Studio' },
  { kind: 'wordmark', label: 'Reverie Agency' },
  { kind: 'badge', label: 'EH', sublabel: 'Epoch Hospitality' },
  { kind: 'wordmark', label: 'Soleil Collective' },
  { kind: 'badge', label: 'NA', sublabel: 'Noire Atelier' },
  { kind: 'wordmark', label: 'Harbour & Co' },
  { kind: 'badge', label: 'AB', sublabel: 'Atlas Brands' },
] as const;

export default function Signals() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.1 });

  return (
    <section
      ref={ref}
      className="bg-stone-900 text-stone-50"
    >
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
        className="flex flex-col"
      >

        {/* ── 1. Stats bar ── */}
        <motion.div
          variants={fadeUp}
          className="border-b border-stone-800"
        >
          <div className="mx-auto flex max-w-screen-xl items-center justify-center divide-x divide-stone-800 px-6 md:px-10 lg:px-16">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="flex flex-1 flex-col items-center gap-1 py-8 text-center"
              >
                <span className="font-display text-[clamp(2.4rem,5vw,4rem)] font-semibold leading-none tracking-[-0.06em] text-stone-50">
                  {stat.value}
                </span>
                <span className="text-[10px] font-medium uppercase tracking-[0.22em] text-stone-500">
                  {stat.label}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* ── 2. Collaborators banner ── */}
        <motion.div
          variants={fadeUp}
          className="border-b border-stone-800 py-5"
        >
          <InfiniteSlider gap={60} duration={45} durationOnHover={90} className="w-full">
            {collaborators.map((item) => (
              <div key={`${item.kind}-${item.label}`} className="flex shrink-0 items-center gap-14">
                {item.kind === 'badge' ? (
                  <div className="flex min-w-[150px] items-center gap-3 border border-[#FF642B]/40 bg-[#FF642B]/10 px-4 py-2 text-[#FF642B]">
                    <span className="flex h-10 w-10 items-center justify-center border border-[#FF642B]/60 text-sm font-bold uppercase tracking-[0.2em]">
                      {item.label}
                    </span>
                    <span className="text-xs font-semibold uppercase tracking-[0.18em]">
                      {item.sublabel}
                    </span>
                  </div>
                ) : (
                  <span className="font-display text-xl font-semibold tracking-[-0.04em] text-[#FF642B] md:text-2xl">
                    {item.label}
                  </span>
                )}
                <span className="select-none text-sm text-[#FF642B]/45">·</span>
              </div>
            ))}
          </InfiniteSlider>
        </motion.div>

      </motion.div>
    </section>
  );
}
