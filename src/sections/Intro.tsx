import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { fadeUp, staggerContainer, lineReveal } from '../lib/motion';

export default function Intro() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.2 });

  return (
    <section
      ref={ref}
      id="about"
      className="bg-white"
    >
      <div className="mx-auto max-w-screen-xl px-6 py-20 md:px-10 md:py-32 lg:px-16">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
        >
          {/* Section label */}
          <motion.div variants={fadeUp} className="flex items-center gap-4 mb-12 md:mb-16">
            <span className="label">Studio</span>
            <motion.div variants={lineReveal} className="h-px flex-1 max-w-[3rem] bg-ink/20" />
          </motion.div>

          {/* Two-column layout */}
          <div className="grid grid-cols-1 gap-12 md:grid-cols-2 md:gap-20">
            {/* LEFT — manifesto */}
            <div className="flex flex-col gap-8">
              <motion.p
                variants={fadeUp}
                className="font-display font-semibold tracking-[-0.04em] text-ink"
              style={{ fontSize: 'clamp(1.8rem, 3.8vw, 3.6rem)', lineHeight: '1.05' }}
              >
                We build brands that feel clear, credible, and premium — from the first interaction.
              </motion.p>

              <motion.p variants={fadeUp} className="text-sm leading-7 text-muted max-w-sm">
                Studio91 works with founders, studios, and growing businesses at key moments:
                launches, repositioning, offer refinement, and digital presence upgrades.
              </motion.p>

              {/* Stat row */}
              <motion.div
                variants={fadeUp}
                className="grid grid-cols-3 gap-8"
              >
                {[
                  { n: '60+', label: 'Projects' },
                  { n: '4', label: 'Years' },
                  { n: '12+', label: 'Countries' },
                ].map((stat) => (
                  <div key={stat.label} className="flex flex-col gap-1">
                    <p className="font-display font-semibold tracking-[-0.05em] text-ink" style={{ fontSize: 'clamp(3rem, 6vw, 5rem)', lineHeight: '1' }}>
                      {stat.n}
                    </p>
                    <p className="label">{stat.label}</p>
                  </div>
                ))}
              </motion.div>

              {/* Disciplines */}
              <motion.div variants={fadeUp} className="flex flex-wrap gap-2">
                {['Branding', 'Strategy', 'Identity Systems', 'Art Direction', 'Campaigns', 'Digital'].map(
                  (d) => (
                    <span
                      key={d}
                      className="border border-ink/15 px-4 py-2 text-[0.65rem] font-medium uppercase tracking-[0.2em] text-muted transition-all duration-300 hover:border-accent hover:text-accent cursor-default"
                    >
                      {d}
                    </span>
                  )
                )}
              </motion.div>
            </div>

            {/* RIGHT — image aggressively cropped */}
            <motion.div variants={fadeUp} className="relative overflow-hidden">
              <div className="h-[480px] md:h-full min-h-[420px] w-full overflow-hidden">
                <img
                  src="https://images.unsplash.com/photo-1497366754035-f200968a6e72?w=1200&q=80&auto=format&fit=crop"
                  alt="Studio91 workspace"
                  className="h-full w-full object-cover grayscale"
                />
                {/* Accent mark */}
                <div className="absolute bottom-0 left-0 h-1 w-16 bg-accent" />
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
