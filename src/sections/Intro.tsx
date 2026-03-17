import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { fadeUp, staggerContainer, lineReveal } from '../lib/motion';

const disciplines = [
  'Branding',
  'Strategy',
  'Identity Systems',
  'Art Direction',
  'Campaigns',
  'Digital',
];

const journey = [
  {
    year: '2020',
    detail:
      'Studio91 was established in London with an early focus on brand identity, visual language, and highly considered execution for emerging businesses.',
  },
  {
    year: '2021',
    detail:
      'The studio expanded into strategy and positioning, with early international mandates and more packaging and art direction work.',
  },
  {
    year: '2022',
    detail:
      'Identity systems, campaigns, and digital experiences became a more visible part of the offer as the studio matured.',
  },
  {
    year: '2023 - Today',
    detail:
      'Studio91 now works across multiple sectors with partners in several regions, balancing clarity, premium positioning, and practical execution.',
  },
];

export default function Intro() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.25 });

  return (
    <section
      ref={ref}
      id="about"
      className="bg-stone-900 px-6 py-16 text-stone-50 md:px-10 md:py-24 lg:px-16"
    >
      <div className="mx-auto max-w-screen-xl">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          className="grid grid-cols-1 gap-10 md:grid-cols-2 md:gap-16"
        >
          {/* LEFT — text content */}
          <div className="flex flex-col gap-8">
            <motion.div variants={fadeUp}>
              <p className="text-xs font-medium uppercase tracking-[0.25em] text-stone-400">
                About
              </p>
              <motion.div variants={lineReveal} className="mt-4 h-px w-12 bg-stone-700" />
            </motion.div>

            <motion.p
              variants={fadeUp}
              className="font-display text-[clamp(2rem,3.6vw,3.2rem)] font-semibold leading-[1.08] tracking-[-0.05em] text-stone-50"
            >
              Studio91 is a creative studio for brands that need to look
              credible, feel intentional, and communicate value from the first
              interaction.
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-base leading-relaxed text-stone-400 md:text-lg"
            >
              We work with founders, studios, and growing businesses at key
              moments: launches, repositioning, offer refinement, and digital
              presence upgrades. The aim is always the same: make the brand
              feel clear, premium, and easy to trust.
            </motion.p>

            <motion.div variants={fadeUp} className="flex flex-wrap gap-3">
              {disciplines.map((discipline) => (
                <span
                  key={discipline}
                  className="cursor-default border border-stone-700 px-4 py-2 text-xs font-medium uppercase tracking-[0.18em] text-stone-300 transition-colors duration-300 hover:border-[#FF642B] hover:text-[#FF9A76]"
                >
                  {discipline}
                </span>
              ))}
            </motion.div>

            {/* Studio story — compact expandable */}
            <motion.details
              variants={fadeUp}
              className="group border-t border-stone-800 pt-6"
            >
              <summary
                data-cursor="hover"
                className="flex cursor-pointer list-none items-center justify-between gap-4"
              >
                <div>
                  <p className="text-xs font-medium uppercase tracking-[0.25em] text-stone-500">
                    Background
                  </p>
                  <p className="mt-1 font-display text-xl font-semibold tracking-[-0.04em] text-stone-50">
                    Read the studio story
                  </p>
                </div>
                <span className="hover-grow-5 border border-stone-700 px-4 py-2 text-xs font-medium uppercase tracking-[0.18em] text-stone-300 transition-colors duration-300 group-hover:border-[#FF642B] group-hover:text-[#FF642B]">
                  Expand
                </span>
              </summary>

              <div className="mt-6 grid gap-4 border-t border-stone-800 pt-6 md:grid-cols-2">
                {journey.map((item) => (
                  <div
                    key={item.year}
                    className="border border-stone-800 bg-stone-900/80 p-5"
                  >
                    <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#FF9A76]">
                      {item.year}
                    </p>
                    <p className="mt-3 text-sm leading-7 text-stone-300">
                      {item.detail}
                    </p>
                  </div>
                ))}
              </div>
            </motion.details>
          </div>

          {/* RIGHT — image */}
          <motion.div
            variants={fadeUp}
            className="relative hidden md:block"
          >
            <div className="sticky top-24 h-[600px] w-full overflow-hidden">
              <img
                src="https://images.unsplash.com/photo-1497366754035-f200968a6e72?w=1200&q=80&auto=format&fit=crop"
                alt="Studio91 workspace"
                className="h-full w-full object-cover grayscale"
              />
              {/* Subtle dark overlay so it doesn't compete with text */}
              <div className="pointer-events-none absolute inset-0 bg-stone-900/30" />
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
