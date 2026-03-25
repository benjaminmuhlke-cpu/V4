import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { staggerContainer, fadeUp } from '../lib/motion';

const testimonials = [
  {
    quote:
      "Studio91 didn't just design our identity. They clarified our positioning and made the brand feel immediately more credible.",
    author: 'Margaux Delacroix',
    role: 'Founder, Maison Verite',
  },
  {
    quote:
      'Working with the team felt like having a creative partner who understood the brief quickly and translated it into sharp, usable direction.',
    author: 'James Osei',
    role: 'Creative Director, Oblique Coffee',
  },
  {
    quote:
      'They turned a complicated brand problem into a clean system our team could actually use. It gave us confidence right away.',
    author: 'Lena Hoffmann',
    role: 'CEO, Forma Collective',
  },
];

export default function Testimonials() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.1 });

  return (
    <section
      ref={ref}
      className="bg-ink py-20 md:py-32"
    >
      <div className="mx-auto max-w-screen-xl px-6 md:px-10 lg:px-16">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
        >
          {/* Header */}
          <div className="mb-16 flex items-end justify-between border-b border-white/10 pb-5">
            <motion.h2
              variants={fadeUp}
              className="font-display font-semibold leading-none tracking-[-0.05em] text-white"
              style={{ fontSize: 'clamp(3rem, 8vw, 8rem)' }}
            >
              Trusted.
            </motion.h2>
            <motion.span variants={fadeUp} className="label hidden text-white/30 md:block">
              Client Words
            </motion.span>
          </div>

          {/* Featured quote — very large */}
          <motion.div variants={fadeUp} className="mb-12 border-b border-white/10 pb-12 md:mb-16 md:pb-16">
            <p className="font-display font-semibold tracking-[-0.04em] text-white" style={{ fontSize: 'clamp(1.5rem, 3.5vw, 3.2rem)', lineHeight: '1.1' }}>
              &ldquo;{testimonials[0].quote}&rdquo;
            </p>
            <div className="mt-6 flex items-center gap-4">
              <div className="h-px w-8 bg-accent" />
              <div>
                <p className="text-sm font-semibold text-white">{testimonials[0].author}</p>
                <p className="label text-white/30 mt-0.5">{testimonials[0].role}</p>
              </div>
            </div>
          </motion.div>

          {/* Two smaller quotes */}
          <motion.div variants={staggerContainer} className="grid grid-cols-1 gap-px bg-white/10 md:grid-cols-2">
            {testimonials.slice(1).map((t) => (
              <motion.div
                key={t.author}
                variants={fadeUp}
                className="bg-ink p-8 md:p-10"
              >
                <p className="text-base leading-relaxed text-white/60 md:text-lg">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <div className="mt-8 flex items-center gap-3 border-t border-white/10 pt-6">
                  <div className="h-px w-5 bg-accent" />
                  <div>
                    <p className="text-sm font-semibold text-white">{t.author}</p>
                    <p className="label text-white/30 mt-0.5">{t.role}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
