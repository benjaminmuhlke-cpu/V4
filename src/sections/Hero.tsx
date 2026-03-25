import { useEffect, useRef, useState } from 'react';
import { motion, useInView } from 'framer-motion';
import { TextScramble } from '../components/ui/text-scramble';
import { staggerContainer, fadeUp } from '../lib/motion';

export default function Hero({ loadingDone = false }: { loadingDone?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.1 });
  const [scrambleTrigger, setScrambleTrigger] = useState(false);
  const [scrambleTriggerSecond, setScrambleTriggerSecond] = useState(false);

  useEffect(() => {
    if (!loadingDone) return;
    const t1 = setTimeout(() => setScrambleTrigger(true), 0);
    const t2 = setTimeout(() => setScrambleTriggerSecond(true), 250);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [loadingDone]);

  return (
    <section
      ref={ref}
      className="relative flex min-h-screen flex-col bg-white"
    >
      {/* Main headline — takes all available vertical space */}
      <div className="mx-auto flex w-full max-w-screen-xl flex-1 flex-col justify-center px-6 py-16 md:px-10 md:py-20 lg:px-16">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          className="flex flex-col gap-0"
        >
          <motion.div variants={fadeUp}>
            <TextScramble
              as="h1"
              trigger={scrambleTrigger}
              duration={2.2}
              speed={0.055}
              className="block font-display font-semibold tracking-[-0.05em] text-ink"
              style={{ fontSize: 'clamp(3.8rem, 11.5vw, 13rem)', lineHeight: '0.88' }}
            >
              Building identities
            </TextScramble>
          </motion.div>

          <motion.div variants={fadeUp}>
            <TextScramble
              as="h1"
              trigger={scrambleTriggerSecond}
              duration={2.2}
              speed={0.055}
              className="block font-display font-semibold tracking-[-0.05em] text-ink"
              style={{ fontSize: 'clamp(3.8rem, 11.5vw, 13rem)', lineHeight: '0.88' }}
            >
              that earn trust fast.
            </TextScramble>
          </motion.div>
        </motion.div>
      </div>

      {/* Bottom editorial strip */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
        className="mx-auto w-full max-w-screen-xl px-6 pb-10 md:px-10 md:pb-14 lg:px-16"
      >
        <motion.div
          variants={fadeUp}
          className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between"
        >
          <p className="max-w-xs text-sm leading-relaxed text-muted">
            Identity, digital presence, and campaign systems
            for founders and growing businesses.
          </p>

          <a
            href="#contact"
            data-cursor="hover"
            className="group inline-flex items-center gap-3 self-start border border-ink px-7 py-3.5 text-xs font-semibold uppercase tracking-[0.2em] text-ink transition-all duration-300 hover:bg-ink hover:text-white md:self-auto"
          >
            Start A Project
            <span className="transition-transform duration-300 group-hover:translate-x-1">→</span>
          </a>
        </motion.div>
      </motion.div>

    </section>
  );
}
