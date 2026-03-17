import { useCallback, useEffect, useRef, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';

type Project = {
  category: string;
  title: string;
  image: string;
};

const slides: Project[] = [
  {
    category: 'Brand Identity',
    title: 'Maison Verite',
    image:
      'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=2000&q=80&auto=format&fit=crop',
  },
  {
    category: 'Packaging + Campaign',
    title: 'Oblique Coffee',
    image:
      'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=2000&q=80&auto=format&fit=crop',
  },
  {
    category: 'Digital Experience',
    title: 'Forma Collective',
    image:
      'https://images.unsplash.com/photo-1494526585095-c41746248156?w=2000&q=80&auto=format&fit=crop',
  },
  {
    category: 'Art Direction',
    title: 'Aura Interiors',
    image:
      'https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=2000&q=80&auto=format&fit=crop',
  },
  {
    category: 'Campaign',
    title: 'Sable FW',
    image:
      'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=2000&q=80&auto=format&fit=crop',
  },
];

const AUTO_ADVANCE_MS = 5000;
const TRANSITION_MS = 2700;

// Extended track: [clone of last, ...real slides, clone of first]
const extendedSlides = [slides[slides.length - 1], ...slides, slides[0]];

export default function ProjectShowcase() {
  const shouldReduceMotion = useReducedMotion();

  // pos is the index within extendedSlides; real slides live at pos 1..slideCount
  const [pos, setPos] = useState(1);
  const [animated, setAnimated] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const resetTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const slideCount = slides.length;

  // Real slide index (for caption + dots)
  const realIndex =
    pos <= 0
      ? slideCount - 1
      : pos >= slideCount + 1
      ? 0
      : pos - 1;

  const activeSlide = slides[realIndex];

  // After reaching a clone, silently jump to the real counterpart
  useEffect(() => {
    if (pos === slideCount + 1) {
      // Just passed the clone of the first slide — jump back to real first
      resetTimer.current = setTimeout(() => {
        setAnimated(false);
        setPos(1);
      }, TRANSITION_MS + 30);
    } else if (pos === 0) {
      // Just passed the clone of the last slide — jump to real last
      resetTimer.current = setTimeout(() => {
        setAnimated(false);
        setPos(slideCount);
      }, TRANSITION_MS + 30);
    }
    return () => {
      if (resetTimer.current) clearTimeout(resetTimer.current);
    };
  }, [pos, slideCount]);

  // Re-enable animation one frame after the silent jump
  useEffect(() => {
    if (!animated) {
      const t = setTimeout(() => setAnimated(true), 50);
      return () => clearTimeout(t);
    }
  }, [animated]);

  const goNext = useCallback(() => {
    setAnimated(true);
    setPos((p) => p + 1);
  }, []);

  const goPrev = useCallback(() => {
    setAnimated(true);
    setPos((p) => p - 1);
  }, []);

  // Auto-advance
  useEffect(() => {
    if (shouldReduceMotion || isPaused) return;
    const id = window.setInterval(goNext, AUTO_ADVANCE_MS);
    return () => window.clearInterval(id);
  }, [isPaused, shouldReduceMotion, goNext]);

  const trackStyle = {
    transform: `translateX(-${pos * 100}%)`,
    transition:
      !animated || shouldReduceMotion
        ? 'none'
        : `transform ${TRANSITION_MS}ms cubic-bezier(0.19, 1, 0.22, 1)`,
  } as const;

  // Click left half → prev, click right half → next
  function handleSliderClick(e: React.MouseEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    if (e.clientX - rect.left < rect.width / 2) {
      goPrev();
    } else {
      goNext();
    }
  }

  return (
    <section id="projects" className="bg-stone-50">
      {/* Header — padded, compact */}
      <div className="mx-auto max-w-screen-xl px-6 pb-8 pt-14 md:px-10 lg:px-16">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-stone-400">
              Selected Projects
            </p>
            <h2 className="mt-3 text-[clamp(2.1rem,4.6vw,4rem)] font-medium leading-[1] tracking-[-0.04em] text-stone-950">
              A few projects.
            </h2>
          </div>
          <p className="max-w-md text-base leading-7 text-stone-500">
            Click left or right to navigate · auto-cycling
          </p>
        </div>
      </div>

      {/* Full-width image slider — edge to edge, 75vh */}
      <motion.div
        initial={{ opacity: 0, y: 18 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: 0.55, ease: [0.19, 1, 0.22, 1] }}
        className="group relative w-full cursor-pointer overflow-hidden"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
        onFocusCapture={() => setIsPaused(true)}
        onBlurCapture={() => setIsPaused(false)}
        onClick={handleSliderClick}
      >
        {/* Track — includes clones on both ends */}
        <div className="flex w-full" style={trackStyle}>
          {extendedSlides.map((slide, i) => (
            <div key={`${slide.title}-${i}`} className="w-full shrink-0">
              <div className="relative h-[55vh] w-full overflow-hidden bg-stone-200 md:h-[75vh]">
                <img
                  src={slide.image}
                  alt={slide.title}
                  className="h-full w-full object-cover"
                  loading="lazy"
                />
              </div>
            </div>
          ))}
        </div>

        {/* Left / right click hint zones — subtle cursor arrows */}
        <div className="pointer-events-none absolute inset-y-0 left-0 flex w-1/2 items-center justify-start pl-6 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          <span className="text-2xl text-white/60">‹</span>
        </div>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex w-1/2 items-center justify-end pr-6 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          <span className="text-2xl text-white/60">›</span>
        </div>

        {/* Bottom-right overlay caption + dots */}
        <div className="absolute bottom-6 right-6 z-10 max-w-[min(360px,calc(100%-3rem))] bg-stone-950/60 p-5 text-right text-stone-50 backdrop-blur-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#FF642B]">
            {activeSlide.category}
          </p>
          <p className="mt-2 text-2xl font-medium tracking-[-0.02em] text-stone-50">
            {activeSlide.title}
          </p>
          <div className="mt-4 flex items-center justify-end gap-2">
            {slides.map((slide, index) => {
              const active = index === realIndex;
              return (
                <button
                  key={slide.title}
                  type="button"
                  aria-label={`Go to project ${index + 1}`}
                  onClick={(e) => {
                    e.stopPropagation(); // don't trigger left/right click
                    setAnimated(true);
                    setPos(index + 1);
                  }}
                  className="h-3 w-3 transition-colors duration-200"
                  style={{
                    backgroundColor: active ? '#FF642B' : '#a8a29e',
                    opacity: active ? 1 : 0.8,
                  }}
                />
              );
            })}
          </div>
        </div>
      </motion.div>
    </section>
  );
}
