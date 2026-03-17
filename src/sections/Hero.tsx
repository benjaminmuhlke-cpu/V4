import { useEffect, useRef, useState } from 'react';
import { motion, useInView } from 'framer-motion';
import { ArrowDownRight } from 'lucide-react';
import { TextScramble } from '../components/ui/text-scramble';
import { fadeUp, staggerContainer } from '../lib/motion';

export default function Hero({ loadingDone = false }: { loadingDone?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.2 });
  const [scrambleTrigger, setScrambleTrigger] = useState(false);
  const [scrambleTriggerSecond, setScrambleTriggerSecond] = useState(false);

  // Fires at 1500ms from App — while loading screen still visible
  useEffect(() => {
    if (!loadingDone) return;
    const timer = setTimeout(() => setScrambleTrigger(true), 0);
    const timerSecond = setTimeout(() => setScrambleTriggerSecond(true), 300);
    return () => {
      clearTimeout(timer);
      clearTimeout(timerSecond);
    };
  }, [loadingDone]);

  return (
    <section
      ref={ref}
      className="relative flex min-h-screen flex-col justify-end bg-stone-50 pb-12 pt-32 md:pb-16"
    >
      <motion.div
        initial={{ scaleX: 0 }}
        animate={isInView ? { scaleX: 1 } : {}}
        transition={{ duration: 1.4, ease: [0.19, 1, 0.22, 1], delay: 0.2 }}
        className="absolute right-0 top-0 h-px w-1/2 origin-right bg-stone-300"
      />

      {/* Container — same padding as every other section */}
      <div className="mx-auto w-full max-w-screen-xl px-6 md:px-10 lg:px-16">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          className="flex flex-col gap-10 md:gap-14"
        >
          {/* Title — right-aligned */}
          <div className="flex flex-col items-end gap-2 text-right">
            <motion.div variants={fadeUp}>
              <TextScramble
                as="h1"
                trigger={scrambleTrigger}
                duration={2.5}
                speed={0.06}
                className="block whitespace-nowrap font-display text-[clamp(3.2rem,8vw,7.2rem)] font-semibold leading-[0.95] tracking-[-0.06em] text-stone-950"
              >
                Building identities
              </TextScramble>
            </motion.div>

            <motion.div variants={fadeUp}>
              <TextScramble
                as="h1"
                trigger={scrambleTriggerSecond}
                duration={2.5}
                speed={0.06}
                className="block whitespace-nowrap font-display text-[clamp(3.2rem,8vw,7.2rem)] font-semibold leading-[0.95] tracking-[-0.06em] text-stone-950"
              >
                that earn trust fast.
              </TextScramble>
            </motion.div>
          </div>

          {/* Bottom row — body text left, CTA button right */}
          <motion.div
            variants={fadeUp}
            className="flex flex-col justify-between gap-8 md:flex-row md:items-end"
          >
            <p className="max-w-lg text-base leading-relaxed text-stone-500 md:text-lg">
              Studio91 shapes clear, credible brands for founders and growing
              businesses across identity, digital presence, and launch
              materials, with a focus on work that feels premium from day one.
            </p>

            <div className="shrink-0">
              <a
                href="#contact"
                data-cursor="hover"
                className="hover-grow-5 group inline-flex items-center gap-2 px-7 py-3.5 text-sm font-semibold uppercase tracking-[0.14em] text-white transition-colors duration-300 hover:bg-[#e55720]"
                style={{ backgroundColor: '#FF642B' }}
              >
                Start A Project
                <ArrowDownRight
                  size={14}
                  className="transition-transform duration-300 group-hover:translate-x-0.5 group-hover:translate-y-0.5"
                />
              </a>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
