import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export default function LoadingScreen({ onComplete }: { onComplete?: () => void }) {
  const [displayText, setDisplayText] = useState('');
  const [isExpanding, setIsExpanding] = useState(false);
  const [isDone, setIsDone] = useState(false);

  const FULL_TEXT = 'STUDIO91';

  useEffect(() => {
    // Start typing at 300ms
    const startDelay = setTimeout(() => {
      let i = 0;
      const typeInterval = setInterval(() => {
        i++;
        setDisplayText(FULL_TEXT.slice(0, i));
        if (i >= FULL_TEXT.length) clearInterval(typeInterval);
      }, 110);
      return () => clearInterval(typeInterval);
    }, 300);

    // Square starts expanding at 1900ms
    const expandTimer = setTimeout(() => setIsExpanding(true), 1900);

    // Notify parent + unmount at 2500ms
    const doneTimer = setTimeout(() => {
      setIsDone(true);
      onComplete?.();
    }, 2500);

    return () => {
      clearTimeout(startDelay);
      clearTimeout(expandTimer);
      clearTimeout(doneTimer);
    };
  }, [onComplete]);

  if (isDone) return null;

  return (
    <motion.div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-stone-950"
      // Fade out the whole overlay after the square has expanded
      animate={isExpanding ? { opacity: 0 } : { opacity: 1 }}
      transition={isExpanding ? { duration: 0.45, delay: 0.35 } : {}}
    >
      <div className="flex flex-col items-center gap-10">

        {/* Square cursor — rotates, then blows up to fill screen */}
        <motion.div
          className="relative flex h-20 w-20 items-center justify-center border-2 border-[#FF642B]"
          animate={
            isExpanding
              ? { scale: 80, rotate: 90 }
              : { rotate: 360 }
          }
          transition={
            isExpanding
              ? { duration: 0.4, ease: [0.19, 1, 0.22, 1] }
              : { duration: 2.5, repeat: Infinity, ease: 'linear' }
          }
        >
          {/* Inner dot — the cursor's center fill */}
          <div className="h-4 w-4 bg-[#FF642B]" />
        </motion.div>

        {/* "STUDIO91" types out below the square */}
        <motion.p
          className="absolute mt-36 font-display text-sm font-semibold tracking-[0.45em] text-stone-400"
          animate={isExpanding ? { opacity: 0, y: -8 } : { opacity: 1, y: 0 }}
          transition={{ duration: 0.18 }}
        >
          {displayText}
          {displayText.length < FULL_TEXT.length && (
            <motion.span
              animate={{ opacity: [1, 0, 1] }}
              transition={{ duration: 0.8, repeat: Infinity }}
            >
              _
            </motion.span>
          )}
        </motion.p>

      </div>
    </motion.div>
  );
}
