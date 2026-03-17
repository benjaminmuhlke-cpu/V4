import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import {
  Layers,
  Fingerprint,
  Camera,
  Package,
  Monitor,
  Megaphone,
} from 'lucide-react';
import { staggerContainer, fadeUp } from '../lib/motion';

const services = [
  {
    icon: Layers,
    title: 'Branding',
    description:
      'Strategic brand development from positioning and messaging to the complete verbal and visual system.',
  },
  {
    icon: Fingerprint,
    title: 'Visual Identity',
    description:
      'Distinctive identity systems — logotype, typography, colour, motion, and the rules that govern them.',
  },
  {
    icon: Camera,
    title: 'Art Direction',
    description:
      'Creative direction for photography, film, and editorial — crafting the image language of a brand.',
  },
  {
    icon: Package,
    title: 'Packaging',
    description:
      'Structural and graphic packaging design that communicates on shelf and in the hands of the customer.',
  },
  {
    icon: Monitor,
    title: 'Digital Experiences',
    description:
      'Websites, web applications, and interactive platforms designed with the same rigour as print.',
  },
  {
    icon: Megaphone,
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
      className="bg-stone-100 py-24 md:py-36"
    >
      <div className="mx-auto max-w-screen-xl px-6 md:px-10 lg:px-16">
        <motion.div
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          variants={staggerContainer}
        >
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-end gap-6 md:gap-20 mb-16 md:mb-24">
            <div className="flex flex-col gap-3 flex-1">
              <motion.p
                variants={fadeUp}
                className="text-xs tracking-[0.25em] uppercase text-stone-400"
              >
                What We Do
              </motion.p>
              <motion.h2
                variants={fadeUp}
                className="font-display text-[clamp(2.5rem,6vw,5.5rem)] leading-tight tracking-tight text-stone-900"
              >
                Our
                <br />
                <em>disciplines.</em>
              </motion.h2>
            </div>
            <motion.p
              variants={fadeUp}
              className="text-stone-500 text-base md:text-lg leading-relaxed max-w-md font-light flex-1"
            >
              We work across the full spectrum of brand-building — from
              foundational strategy to the finest details of execution.
              Every discipline connected by a unified creative intelligence.
            </motion.p>
          </div>

          {/* Service grid */}
          <motion.div
            variants={staggerContainer}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px bg-stone-300"
          >
            {services.map((service) => {
              const Icon = service.icon;
              return (
                <motion.div
                  key={service.title}
                  variants={fadeUp}
                  className="bg-stone-100 p-8 md:p-10 flex flex-col gap-5 group hover:bg-stone-50 transition-colors duration-300"
                >
                  <div className="flex items-center justify-between">
                    <div className="w-10 h-10 flex items-center justify-center border border-stone-300 group-hover:border-stone-900 transition-colors duration-300">
                      <Icon size={18} className="text-stone-600 group-hover:text-stone-900 transition-colors duration-300" />
                    </div>
                  </div>
                  <div className="flex flex-col gap-2">
                    <h3 className="font-display text-xl tracking-tight text-stone-900">
                      {service.title}
                    </h3>
                    <p className="text-sm text-stone-500 leading-relaxed font-light">
                      {service.description}
                    </p>
                  </div>
                  <div className="mt-auto pt-4">
                    <span className="text-xs tracking-widest uppercase text-stone-400 group-hover:text-stone-700 transition-colors duration-300">
                      Learn more →
                    </span>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
