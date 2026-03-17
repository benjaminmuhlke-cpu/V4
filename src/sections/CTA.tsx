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
  const isInView = useInView(ref, { once: true, amount: 0.3 });
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
        headers: {
          Accept: 'application/json',
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Submission failed');
      }

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
      className="bg-stone-50 py-16 md:py-24"
    >
      <div className="mx-auto max-w-screen-xl px-6 md:px-10 lg:px-16">
        <motion.div
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          variants={staggerContainer}
          className="grid gap-12 rounded-[2rem] border border-stone-200 bg-white p-8 md:grid-cols-[0.9fr_1.1fr] md:gap-16 md:p-12"
        >
          <div className="flex flex-col gap-6">
            <motion.p
              variants={fadeUp}
              className="text-xs font-medium uppercase tracking-[0.25em] text-stone-400"
            >
              Contact
            </motion.p>

            <motion.h2
              variants={fadeUp}
              className="font-display text-[clamp(2.4rem,6vw,5rem)] font-semibold leading-[0.95] tracking-[-0.05em] text-stone-950"
            >
              Tell us what you need,
              <br />
              we&apos;ll get back to you ASAP.
            </motion.h2>

            <motion.p
              variants={fadeUp}
              className="max-w-md text-base leading-8 text-stone-500"
            >
              Share your basic contact info, a short description of the
              project, and your budget range. Form submissions are set up for
              <span className="font-medium text-stone-700"> naiwen1991@gmail.com</span>.
            </motion.p>

            <motion.div
              variants={fadeUp}
              className="rounded-2xl border border-dashed border-stone-300 bg-stone-50 p-5 text-sm leading-7 text-stone-500"
            >
              Replace the placeholder Formspree endpoint in this component with
              your live form ID before launch.
            </motion.div>
          </div>

          <motion.form variants={fadeUp} onSubmit={handleSubmit} className="grid gap-5">
            <div className="grid gap-5 md:grid-cols-2">
              <label className="grid gap-2 text-sm font-medium text-stone-700">
                Name
                <input
                  required
                  name="name"
                  type="text"
                  className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3.5 text-base text-stone-900 outline-none transition-colors duration-200 placeholder:text-stone-400 focus:border-[#FF642B]"
                  placeholder="Your name"
                />
              </label>

              <label className="grid gap-2 text-sm font-medium text-stone-700">
                Email
                <input
                  required
                  name="email"
                  type="email"
                  className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3.5 text-base text-stone-900 outline-none transition-colors duration-200 placeholder:text-stone-400 focus:border-[#FF642B]"
                  placeholder="you@example.com"
                />
              </label>
            </div>

            <label className="grid gap-2 text-sm font-medium text-stone-700">
              Company / Brand
              <input
                name="company"
                type="text"
                className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3.5 text-base text-stone-900 outline-none transition-colors duration-200 placeholder:text-stone-400 focus:border-[#FF642B]"
                placeholder="Optional"
              />
            </label>

            <label className="grid gap-2 text-sm font-medium text-stone-700">
              What do you need?
              <textarea
                required
                name="projectNeed"
                rows={5}
                className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3.5 text-base text-stone-900 outline-none transition-colors duration-200 placeholder:text-stone-400 focus:border-[#FF642B]"
                placeholder="Briefly describe your project, goals, and timeline."
              />
            </label>

            <label className="grid gap-2 text-sm font-medium text-stone-700">
              Budget
              <select
                required
                name="budget"
                defaultValue=""
                className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3.5 text-base text-stone-900 outline-none transition-colors duration-200 focus:border-[#FF642B]"
              >
                <option value="" disabled>
                  Select a budget range
                </option>
                {budgetOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>

            <div className="flex flex-col gap-3 pt-2">
              <button
                type="submit"
                disabled={status === 'submitting'}
                data-cursor="hover"
                className="hover-grow-5 inline-flex items-center justify-center rounded-full bg-[#FF642B] px-6 py-4 text-sm font-semibold uppercase tracking-[0.16em] text-white transition-colors duration-300 hover:bg-[#e55720] disabled:cursor-not-allowed disabled:bg-[#ff9a76]"
              >
                {status === 'submitting' ? 'Sending...' : 'Send Inquiry'}
              </button>

              {status === 'success' && (
                <p className="text-sm text-emerald-600">
                  Thanks. Your inquiry was sent successfully.
                </p>
              )}

              {status === 'error' && (
                <p className="text-sm text-red-600">
                  Something went wrong. Please try again after updating the
                  Formspree endpoint.
                </p>
              )}
            </div>
          </motion.form>
        </motion.div>
      </div>

      <motion.div
        initial={{ scaleX: 0, originX: 0.5 }}
        animate={isInView ? { scaleX: 1 } : {}}
        transition={{ duration: 1.4, ease: [0.19, 1, 0.22, 1], delay: 0.5 }}
        className="mx-auto mt-24 h-px max-w-screen-xl bg-stone-200"
      />
    </section>
  );
}
