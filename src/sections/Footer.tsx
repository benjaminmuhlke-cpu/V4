export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="bg-ink px-6 py-6 md:px-10 lg:px-16">
      <div className="mx-auto max-w-screen-xl">
        <div className="flex flex-col gap-3 border-t border-white/10 pt-6 md:flex-row md:items-center md:justify-between">
          <p className="font-display text-sm font-semibold tracking-[-0.03em] text-white">
            Studio91
          </p>
          <div className="flex items-center gap-6">
            <a href="#projects" className="label text-white/30 transition-colors duration-300 hover:text-white/70">
              Work
            </a>
            <a href="#services" className="label text-white/30 transition-colors duration-300 hover:text-white/70">
              Services
            </a>
            <a href="#contact" className="label text-white/30 transition-colors duration-300 hover:text-white/70">
              Contact
            </a>
          </div>
          <p className="label text-white/20">
            © {year} Studio91. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
