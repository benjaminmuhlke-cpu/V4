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
      className="bg-stone-900 py-16 text-stone-50 md:py-24"
    >
      <div className="mx-auto max-w-screen-xl px-6 md:px-10 lg:px-16">
        <motion.div
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          variants={staggerContainer}
        >
          <div className="mb-12 flex flex-col gap-3 md:mb-16">
            <motion.p
              variants={fadeUp}
              className="text-xs font-medium uppercase tracking-[0.25em] text-stone-500"
            >
              Trusted By Founders
            </motion.p>
            <motion.h2
              variants={fadeUp}
              className="font-display max-w-4xl text-[clamp(2.2rem,5vw,4.75rem)] font-semibold leading-[1] tracking-[-0.05em] text-stone-50"
            >
              Social proof that helps clients
              <br />
              trust the process quickly.
            </motion.h2>
          </div>

          <motion.div
            variants={staggerContainer}
            className="grid grid-cols-1 gap-px bg-stone-800 md:grid-cols-3"
          >
            {testimonials.map((testimonial) => (
              <motion.div
                key={testimonial.author}
                variants={fadeUp}
                className="group flex flex-col justify-between gap-10 bg-stone-900 p-8 transition-colors duration-400 hover:bg-stone-800 md:p-10"
              >
                <p className="text-lg leading-relaxed text-stone-200 md:text-xl">
                  &quot;{testimonial.quote}&quot;
                </p>
                <div className="flex flex-col gap-1 border-t border-stone-800 pt-4 transition-colors duration-300 group-hover:border-stone-700">
                  <span className="text-sm font-semibold text-stone-50">
                    {testimonial.author}
                  </span>
                  <span className="text-xs tracking-wide text-stone-500">
                    {testimonial.role}
                  </span>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

