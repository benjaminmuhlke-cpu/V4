import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { Globe } from '../components/ui/globe';
import { staggerContainer, fadeUp } from '../lib/motion';

const highlightedCities = ['Shanghai', 'Taipei', 'Paris'];

export default function GlobalReach() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.2 });

  return (
    <section
      ref={ref}
      id="reach"
      className="relative flex items-center overflow-hidden bg-stone-900 py-16 md:min-h-[380px] md:py-0"
    >
      <div className="mx-auto w-full max-w-screen-xl px-6 md:px-10 lg:px-16">
        <div className="grid grid-cols-1 items-center gap-12 md:grid-cols-2 md:gap-0">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate={isInView ? 'visible' : 'hidden'}
            className="relative z-10 flex flex-col gap-7 py-10 md:py-16"
          >
            <motion.p
              variants={fadeUp}
              className="text-xs font-medium uppercase tracking-[0.25em] text-stone-500"
            >
              Global Inspiration
            </motion.p>

            <motion.h2
              variants={fadeUp}
              className="font-display text-[clamp(2.2rem,5vw,4.25rem)] font-semibold leading-[1.02] tracking-[-0.05em] text-stone-50"
            >
              A glocal point of view, shaped by world capitals.
            </motion.h2>

            <motion.p
              variants={fadeUp}
              className="max-w-md text-base leading-relaxed text-stone-400 md:text-lg"
            >
              Studio91 draws inspiration from the rhythm, restraint, and energy
              of capitals across Asia, Europe, and the US. We go deepest on
              Shanghai, Taipei, and Paris, with additional reference points
              from Amsterdam, Berlin, New York, Los Angeles, and Tokyo.
            </motion.p>

            <motion.div variants={fadeUp} className="mt-2 flex flex-wrap gap-3">
              {highlightedCities.map((city) => (
                <span
                  key={city}
                  className="cursor-default border border-stone-800 px-3 py-1.5 text-[10px] font-medium uppercase tracking-[0.18em] text-stone-500 transition-colors duration-300 hover:border-[#FF642B] hover:text-[#FF9A76]"
                >
                  {city}
                </span>
              ))}
            </motion.div>
          </motion.div>

          <div className="relative hidden h-[300px] items-center justify-center md:flex">
            <div className="pointer-events-none absolute inset-0 z-10 [background:radial-gradient(ellipse_50%_50%_at_50%_50%,transparent_40%,#1c1917_100%)]" />
            <Globe className="top-1/2 max-w-[210px] -translate-y-1/2" />
          </div>
        </div>
      </div>

      <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-stone-50 to-transparent" />
    </section>
  );
}
