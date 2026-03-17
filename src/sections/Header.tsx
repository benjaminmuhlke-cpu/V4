import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Menu } from 'lucide-react';

const navLinks = [
  { label: 'Projects', href: '#projects' },
  { label: 'Services', href: '#services' },
  { label: 'Who We Are', href: '#about' },
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
          scrolled
            ? 'border-b border-stone-200 bg-stone-50/90 backdrop-blur-md'
            : 'bg-transparent'
        }`}
      >
        <div className="mx-auto max-w-screen-xl px-6 md:px-10 lg:px-16">
          <div className="flex h-16 items-center justify-between md:h-20">
            <a
              href="#"
              className="font-display text-xl font-bold tracking-[-0.04em] text-[#FF642B] transition-opacity duration-300 hover:opacity-80 md:text-2xl"
            >
              Studio91
            </a>

            {/* Desktop nav */}
            <nav className="hidden items-center gap-10 md:flex">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="group relative text-sm font-medium uppercase tracking-[0.16em] text-stone-500 transition-colors duration-300 hover:text-stone-950"
                >
                  {link.label}
                  <span className="absolute -bottom-1 left-0 h-px w-0 bg-[#FF642B] transition-all duration-300 ease-out group-hover:w-full" />
                </a>
              ))}
            </nav>

            <div className="hidden items-center gap-4 md:flex">
              <a
                href="#contact"
                data-cursor="hover"
                className="hover-grow-5 inline-flex items-center px-5 py-2.5 text-sm font-medium text-white transition-colors duration-300 hover:bg-[#e55720]"
                style={{ backgroundColor: '#FF642B' }}
              >
                Let's Talk
              </a>
            </div>

            <button
              className="p-1 text-stone-900 md:hidden"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Toggle menu"
            >
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </motion.header>

      {/* Mobile menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4, ease: [0.19, 1, 0.22, 1] }}
            className="fixed inset-0 z-40 flex flex-col bg-stone-50 px-6 pt-20 md:hidden"
          >
            <nav className="mt-8 flex flex-col gap-8">
              {navLinks.map((link, i) => (
                <motion.a
                  key={link.label}
                  href={link.href}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.07, duration: 0.5, ease: [0.19, 1, 0.22, 1] }}
                  onClick={() => setMenuOpen(false)}
                  className="font-display text-4xl font-semibold tracking-[-0.04em] text-stone-950 transition-colors duration-300 hover:text-[#FF642B]"
                >
                  {link.label}
                </motion.a>
              ))}
              <motion.a
                href="#contact"
                data-cursor="hover"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.35, duration: 0.5 }}
                onClick={() => setMenuOpen(false)}
                className="hover-grow-5 mt-4 inline-flex self-start px-8 py-4 text-sm font-medium text-white transition-colors duration-300 hover:bg-[#e55720]"
                style={{ backgroundColor: '#FF642B' }}
              >
                Let's Talk
              </motion.a>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
