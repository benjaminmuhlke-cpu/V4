import { useRef } from 'react';
import type React from 'react';
import { motion, useInView } from 'framer-motion';
import { fadeUp, staggerContainer } from '../lib/motion';

type Project = {
  index: string;
  category: string;
  title: string;
  image: string;
  year: string;
};

const projects: Project[] = [
  {
    index: '01',
    category: 'Brand Identity',
    title: 'Maison Verite',
    year: '2024',
    image:
      'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=2000&q=80&auto=format&fit=crop',
  },
  {
    index: '02',
    category: 'Packaging + Campaign',
    title: 'Oblique Coffee',
    year: '2024',
    image:
      'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=2000&q=80&auto=format&fit=crop',
  },
  {
    index: '03',
    category: 'Digital Experience',
    title: 'Forma Collective',
    year: '2023',
    image:
      'https://images.unsplash.com/photo-1494526585095-c41746248156?w=2000&q=80&auto=format&fit=crop',
  },
  {
    index: '04',
    category: 'Art Direction',
    title: 'Aura Interiors',
    year: '2023',
    image:
      'https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=2000&q=80&auto=format&fit=crop',
  },
];

function ProjectCard({
  project,
  className,
  imageClass,
  style,
}: {
  project: Project;
  className?: string;
  imageClass?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div className={`group relative overflow-hidden bg-dark ${className}`} style={style}>
      <img
        src={project.image}
        alt={project.title}
        className={`h-full w-full object-cover grayscale transition-all duration-700 group-hover:grayscale-0 group-hover:scale-[1.03] ${imageClass ?? ''}`}
        loading="lazy"
      />
      {/* Overlay */}
      <div className="absolute inset-0 bg-ink/20 transition-opacity duration-500 group-hover:opacity-0" />
      {/* Caption strip */}
      <div className="absolute bottom-0 left-0 right-0 flex items-end justify-between p-5 md:p-6">
        <div>
          <p className="label text-white/60">{project.category}</p>
          <p className="mt-1 font-display text-lg font-semibold leading-tight tracking-[-0.03em] text-white md:text-xl">
            {project.title}
          </p>
        </div>
        <span className="font-mono text-3xl font-semibold leading-none text-white/20 md:text-4xl">
          {project.index}
        </span>
      </div>
    </div>
  );
}

export default function ProjectShowcase() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.1 });

  return (
    <section id="projects" ref={ref} className="bg-white">
      {/* Section header */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
        className="mx-auto max-w-screen-xl px-6 pb-8 pt-20 md:px-10 md:pt-28 lg:px-16"
      >
        <div className="flex items-end justify-between border-b border-ink/10 pb-5">
          <motion.h2
            variants={fadeUp}
            className="font-display font-semibold leading-none tracking-[-0.05em] text-ink"
            style={{ fontSize: 'clamp(3rem, 8vw, 8rem)' }}
          >
            Work.
          </motion.h2>
          <motion.span variants={fadeUp} className="label hidden md:block">
            Selected Projects
          </motion.span>
        </div>
      </motion.div>

      {/* Editorial image grid */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
        className="w-full"
      >
        {/* Row 1: large left (7fr) + right (5fr) */}
        <motion.div
          variants={fadeUp}
          className="grid grid-cols-1 gap-px bg-ink"
          style={{ gridTemplateColumns: '7fr 5fr' }}
        >
          <ProjectCard project={projects[0]} className="h-[55vw] w-full" style={{ maxHeight: '70vh' }} />
          <ProjectCard project={projects[1]} className="h-[55vw] w-full" style={{ maxHeight: '70vh' }} />
        </motion.div>

        {/* Row 2: two equal halves */}
        <motion.div
          variants={fadeUp}
          className="grid grid-cols-1 gap-px bg-ink"
          style={{ gridTemplateColumns: '1fr 1fr' }}
        >
          <ProjectCard project={projects[2]} className="w-full" style={{ height: '40vw', maxHeight: '55vh' }} />
          <ProjectCard project={projects[3]} className="w-full" style={{ height: '40vw', maxHeight: '55vh' }} />
        </motion.div>
      </motion.div>

      {/* View all link */}
      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
        className="mx-auto max-w-screen-xl px-6 py-10 md:px-10 lg:px-16"
      >
        <a
          href="#"
          className="group inline-flex items-center gap-3 label text-ink transition-opacity duration-300 hover:opacity-50"
        >
          All Projects
          <span className="transition-transform duration-300 group-hover:translate-x-1">→</span>
        </a>
      </motion.div>
    </section>
  );
}
