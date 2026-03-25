import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { staggerContainer, fadeUp } from '../lib/motion';

const services = [
  {
    index: '01',
    title: 'Branding',
    description:
      'Strategic brand development from positioning and messaging to the complete verbal and visual system.',
  },
  {
    index: '02',
    title: 'Visual Identity',
    description:
      'Distinctive identity systems — logotype, typography, colour, motion, and the rules that govern them.',
  },
  {
    index: '03',
    title: 'Art Direction',
    description:
      'Creative direction for photography, film, and editorial — crafting the image language of a brand.',
  },
  {
    index: '04',
    title: 'Packaging',
    description:
      'Structural and graphic packaging design that communicates on shelf and in the hands of the customer.',
  },
  {
    index: '05',
    title: 'Digital Experiences',
    description:
      'Websites, web applications, and interactive platforms designed with the same rigour as print.',
  },
  {
    index: '06',
    title: 'Campaign Systems',
    description:
      'Integrated campaign concepts and executions across channels, built on a singular creative idea.',
  },
];

export default function Services() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.1 });

  return (
    <section
      ref={ref}
      id="services"
      className="bg-ink py-20 md:py-32"
    >
      <div className="mx-auto max-w-screen-xl px-6 md:px-10 lg:px-16">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
        >
          {/* Section header */}
          <div className="mb-16 flex items-end justify-between border-b border-white/10 pb-5 md:mb-20">
            <motion.h2
              variants={fadeUp}
              className="font-display font-semibold leading-none tracking-[-0.05em] text-white"
              style={{ fontSize: 'clamp(3rem, 8vw, 8rem)' }}
            >
              Disciplines.
            </motion.h2>
            <motion.span variants={fadeUp} className="label hidden text-white/40 md:block">
              What We Do
            </motion.span>
          </div>

          {/* Service rows — editorial numbered list */}
          <motion.div variants={staggerContainer} className="flex flex-col">
            {services.map((service) => (
              <motion.div
                key={service.index}
                variants={fadeUp}
                className="group grid cursor-default grid-cols-[3rem_1fr] gap-4 border-b border-white/10 py-7 transition-colors duration-300 hover:border-white/20 md:grid-cols-[4rem_1fr_1fr] md:gap-8 md:py-8"
              >
                {/* Index */}
                <span className="font-mono text-xs font-medium text-accent mt-1">
                  {service.index}
                </span>

                {/* Title */}
                <h3 className="font-display text-2xl font-semibold tracking-[-0.03em] text-white transition-colors duration-300 group-hover:text-accent md:text-3xl">
                  {service.title}
                </h3>

                {/* Description — hidden on mobile, shown on md+ */}
                <p className="hidden text-sm leading-relaxed text-white/40 md:block md:max-w-sm">
                  {service.description}
                </p>
              </motion.div>
            ))}
          </motion.div>

          {/* Bottom tag */}
          <motion.p variants={fadeUp} className="mt-10 label text-white/30">
            Full-spectrum brand execution — strategy through production.
          </motion.p>
        </motion.div>
      </div>
    </section>
  );
}
