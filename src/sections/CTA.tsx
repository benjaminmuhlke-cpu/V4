import { FormEvent, useRef, useState } from 'react';
import { motion, useInView } from 'framer-motion';
import { staggerContainer, fadeUp } from '../lib/motion';

const FORMSPREE_ENDPOINT = 'https://formspree.io/f/your-form-id';

const budgetOptions = [
  'Under $1,000',
  '$1,000 - $3,000',
  '$3,000 - $5,000',
  '$5,000 - $10,000',
  '$10,000+',
];

export default function CTA() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.2 });
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus('submitting');
    const form = event.currentTarget;
    const formData = new FormData(form);
    formData.append('_subject', 'New Studio91 inquiry');
    try {
      const response = await fetch(FORMSPREE_ENDPOINT, {
        method: 'POST',
        headers: { Accept: 'application/json' },
        body: formData,
      });
      if (!response.ok) throw new Error('failed');
      form.reset();
      setStatus('success');
    } catch {
      setStatus('error');
    }
  }

  return (
    <section
      ref={ref}
      id="contact"
      className="bg-white"
    >
      {/* Full-width black header bar */}
      <div className="bg-ink px-6 py-16 md:px-10 md:py-24 lg:px-16">
        <div className="mx-auto max-w-screen-xl">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate={isInView ? 'visible' : 'hidden'}
            className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between"
          >
            <motion.h2
              variants={fadeUp}
              className="font-display font-semibold tracking-[-0.05em] text-white"
              style={{ fontSize: 'clamp(3.2rem, 9vw, 9.5rem)', lineHeight: '0.88' }}
            >
              Start A<br />Project.
            </motion.h2>
            <motion.p variants={fadeUp} className="max-w-xs text-sm leading-relaxed text-white/40 md:text-right">
              Share your project brief and budget range.
              We respond to every inquiry within 48 hours.
            </motion.p>
          </motion.div>
        </div>
      </div>

      {/* Form section — white */}
      <div className="mx-auto max-w-screen-xl px-6 py-14 md:px-10 md:py-20 lg:px-16">
        <motion.form
          variants={staggerContainer}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          onSubmit={handleSubmit}
          className="grid gap-0 border border-ink/10 md:grid-cols-2"
        >
          {/* Name */}
          <motion.label variants={fadeUp} className="grid gap-2 border-b border-ink/10 p-6 md:border-r">
            <span className="label">Name *</span>
            <input
              required
              name="name"
              type="text"
              className="border-none bg-transparent text-base text-ink outline-none placeholder:text-ink/25 focus:outline-none"
              placeholder="Your name"
            />
          </motion.label>

          {/* Email */}
          <motion.label variants={fadeUp} className="grid gap-2 border-b border-ink/10 p-6">
            <span className="label">Email *</span>
            <input
              required
              name="email"
              type="email"
              className="border-none bg-transparent text-base text-ink outline-none placeholder:text-ink/25 focus:outline-none"
              placeholder="you@example.com"
            />
          </motion.label>

          {/* Company */}
          <motion.label variants={fadeUp} className="grid gap-2 border-b border-ink/10 p-6 md:border-r">
            <span className="label">Company / Brand</span>
            <input
              name="company"
              type="text"
              className="border-none bg-transparent text-base text-ink outline-none placeholder:text-ink/25 focus:outline-none"
              placeholder="Optional"
            />
          </motion.label>

          {/* Budget */}
          <motion.label variants={fadeUp} className="grid gap-2 border-b border-ink/10 p-6">
            <span className="label">Budget Range *</span>
            <select
              required
              name="budget"
              defaultValue=""
              className="border-none bg-transparent text-base text-ink outline-none focus:outline-none"
            >
              <option value="" disabled className="text-ink/30">
                Select a range
              </option>
              {budgetOptions.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          </motion.label>

          {/* Message */}
          <motion.label variants={fadeUp} className="grid gap-2 border-b border-ink/10 p-6 md:col-span-2">
            <span className="label">Project Brief *</span>
            <textarea
              required
              name="projectNeed"
              rows={5}
              className="border-none bg-transparent text-base text-ink outline-none placeholder:text-ink/25 focus:outline-none resize-none"
              placeholder="Describe your project, goals, and timeline."
            />
          </motion.label>

          {/* Submit row */}
          <motion.div variants={fadeUp} className="flex items-center justify-between p-6 md:col-span-2">
            <p className="label text-ink/30 hidden md:block">
              Submissions go to{' '}
              <span className="text-ink/60">naiwen1991@gmail.com</span>
            </p>
            <div className="flex flex-col gap-2 w-full md:w-auto md:items-end">
              <button
                type="submit"
                disabled={status === 'submitting'}
                data-cursor="hover"
                className="group inline-flex items-center gap-3 bg-ink px-8 py-4 text-xs font-semibold uppercase tracking-[0.2em] text-white transition-all duration-300 hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed w-full justify-center md:w-auto"
              >
                {status === 'submitting' ? 'Sending...' : 'Send Inquiry'}
                <span className="transition-transform duration-300 group-hover:translate-x-1">→</span>
              </button>

              {status === 'success' && (
                <p className="text-xs text-emerald-600 tracking-wide">Inquiry sent successfully.</p>
              )}
              {status === 'error' && (
                <p className="text-xs text-red-500 tracking-wide">Something went wrong. Please try again.</p>
              )}
            </div>
          </motion.div>
        </motion.form>
      </div>
    </section>
  );
}
