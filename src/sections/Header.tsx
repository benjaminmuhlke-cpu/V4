import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const navLinks = [
  { label: 'Work', href: '#projects' },
  { label: 'Services', href: '#services' },
  { label: 'Studio', href: '#about' },
];

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', handler, { passive: true });
    return () => window.removeEventListener('scroll', handler);
  }, []);

  return (
    <>
      <motion.header
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.19, 1, 0.22, 1] }}
        className={`fixed left-0 right-0 top-0 z-50 transition-all duration-500 ${
          scrolled ? 'border-b border-ink/10 bg-white/95 backdrop-blur-sm' : 'bg-transparent'
        }`}
      >
        <div className="mx-auto max-w-screen-xl px-6 md:px-10 lg:px-16">
          <div className="flex h-14 items-center justify-between md:h-16">
            <a
              href="#"
              className="font-display text-base font-semibold tracking-[-0.04em] text-ink transition-opacity duration-300 hover:opacity-50"
            >
              Studio91
            </a>

            {/* Desktop nav — all right */}
            <div className="hidden items-center gap-10 md:flex">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="label link-line text-ink hover:text-ink transition-opacity duration-300 hover:opacity-60"
                >
                  {link.label}
                </a>
              ))}
              <a
                href="#contact"
                data-cursor="hover"
                className="label text-ink transition-opacity duration-300 hover:opacity-50"
              >
                Contact ↗
              </a>
            </div>

            <button
              className="flex h-8 w-8 flex-col items-center justify-center gap-[5px] text-ink md:hidden"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Toggle menu"
            >
              <span
                className={`block h-px w-6 bg-current transition-all duration-300 ${menuOpen ? 'translate-y-[7px] rotate-45' : ''}`}
              />
              <span
                className={`block h-px w-6 bg-current transition-all duration-300 ${menuOpen ? 'opacity-0' : ''}`}
              />
              <span
                className={`block h-px w-6 bg-current transition-all duration-300 ${menuOpen ? '-translate-y-[7px] -rotate-45' : ''}`}
              />
            </button>
          </div>
        </div>
      </motion.header>

      {/* Mobile menu — full black overlay */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35, ease: [0.19, 1, 0.22, 1] }}
            className="fixed inset-0 z-40 flex flex-col bg-ink px-6 pt-20 md:hidden"
          >
            <nav className="mt-8 flex flex-col gap-0 border-t border-white/10">
              {navLinks.map((link, i) => (
                <motion.a
                  key={link.label}
                  href={link.href}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.07, duration: 0.5, ease: [0.19, 1, 0.22, 1] }}
                  onClick={() => setMenuOpen(false)}
                  className="border-b border-white/10 py-7 font-display text-5xl font-semibold tracking-[-0.04em] text-white transition-colors duration-300 hover:text-accent"
                >
                  {link.label}
                </motion.a>
              ))}
              <motion.a
                href="#contact"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.35, duration: 0.5 }}
                onClick={() => setMenuOpen(false)}
                className="mt-8 inline-flex self-start border border-white/20 px-8 py-4 text-xs font-medium uppercase tracking-[0.2em] text-white transition-colors duration-300 hover:border-accent hover:text-accent"
              >
                Contact ↗
              </motion.a>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
