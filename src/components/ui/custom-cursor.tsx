import { useEffect, useMemo, useRef, useState } from "react";

export default function CustomCursor() {
  const [hovered, setHovered] = useState(false);
  const [clicked, setClicked] = useState(false);
  const [visible, setVisible] = useState(false);

  const cursorRef = useRef<HTMLDivElement>(null);
  const dotRef = useRef<HTMLDivElement>(null);

  const targetPosRef = useRef({ x: -100, y: -100 });
  const displayPosRef = useRef({ x: -100, y: -100 });

  const orange = "#ff642b";

  const { size, dotSize } = useMemo(() => {
    const base = 38;
    const hoverScale = 1.15; // +15% on clickable hover
    const clickScale = 0.8;

    const scaled =
      (clicked ? base * clickScale : hovered ? base * hoverScale : base) | 0;

    const baseDot = 6;
    const scaledDot =
      (clicked
        ? baseDot * 0.85
        : hovered
          ? baseDot * 1.15
          : baseDot) | 0;

    return { size: scaled, dotSize: scaledDot };
  }, [clicked, hovered]);

  useEffect(() => {
    const supportsHover =
      typeof window !== "undefined" &&
      window.matchMedia?.("(hover: hover) and (pointer: fine)")?.matches;

    if (!supportsHover) return;

    const moveCursor = (e: MouseEvent) => {
      targetPosRef.current = { x: e.clientX, y: e.clientY };
      setVisible(true);
    };

    const isClickable = (element: HTMLElement | null) => {
      if (!element) return false;

      const interactive = element.closest(
        "a, button, input, textarea, select, summary, label, [role='button'], [data-cursor='hover']",
      ) as HTMLElement | null;

      const candidate = interactive ?? element;

      const disabled =
        candidate.matches?.(":disabled") ||
        candidate.getAttribute?.("aria-disabled") === "true";
      if (disabled) return false;

      // Treat anything styled like a pointer as clickable.
      const cursorStyle = window.getComputedStyle(candidate).cursor;
      if (cursorStyle === "pointer") return true;

      // Otherwise require known interactive selector.
      return Boolean(interactive);
    };

    const handleMouseOver = (e: Event) => {
      const target = e.target as HTMLElement | null;
      setHovered(isClickable(target));
    };

    const handleMouseDown = () => setClicked(true);
    const handleMouseUp = () => setClicked(false);
    const handleMouseLeave = () => setVisible(false);
    const handleMouseEnter = () => setVisible(true);

    window.addEventListener("mousemove", moveCursor);
    document.addEventListener("mouseover", handleMouseOver);
    window.addEventListener("mousedown", handleMouseDown);
    window.addEventListener("mouseup", handleMouseUp);
    document.addEventListener("mouseleave", handleMouseLeave);
    document.addEventListener("mouseenter", handleMouseEnter);

    return () => {
      window.removeEventListener("mousemove", moveCursor);
      document.removeEventListener("mouseover", handleMouseOver);
      window.removeEventListener("mousedown", handleMouseDown);
      window.removeEventListener("mouseup", handleMouseUp);
      document.removeEventListener("mouseleave", handleMouseLeave);
      document.removeEventListener("mouseenter", handleMouseEnter);
    };
  }, []);

  useEffect(() => {
    let animationFrameId = 0;

    // Higher = more reactive (less lag). 0.35 feels snappy without jitter.
    const follow = 0.35;

    const animate = () => {
      const t = targetPosRef.current;
      const d = displayPosRef.current;

      const nx = d.x + (t.x - d.x) * follow;
      const ny = d.y + (t.y - d.y) * follow;

      displayPosRef.current = { x: nx, y: ny };

      const cursor = cursorRef.current;
      const dot = dotRef.current;
      if (cursor) cursor.style.transform = `translate3d(${nx}px, ${ny}px, 0)`;
      if (dot) dot.style.transform = `translate3d(${nx}px, ${ny}px, 0)`;

      animationFrameId = requestAnimationFrame(animate);
    };

    animationFrameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  return (
    <>
      <style>{`
        html, body, * {
          cursor: none !important;
        }

        @media (max-width: 768px), (pointer: coarse) {
          .studio91-custom-cursor,
          .studio91-custom-cursor-dot {
            display: none !important;
          }

          html, body, * {
            cursor: auto !important;
          }
        }
      `}</style>

      <div
        ref={cursorRef}
        className="studio91-custom-cursor"
        style={{
          position: "fixed",
          left: 0,
          top: 0,
          width: size,
          height: size,
          border: `2px solid ${orange}`,
          borderRadius: 0,
          backgroundColor: hovered ? "rgba(255, 100, 43, 0.14)" : "transparent",
          transition:
            "width 0.22s ease, height 0.22s ease, background-color 0.22s ease, opacity 0.2s ease",
          pointerEvents: "none",
          zIndex: 9999,
          opacity: visible ? 1 : 0,
          mixBlendMode: "normal",
          marginLeft: -size / 2,
          marginTop: -size / 2,
          willChange: "transform, width, height, opacity",
        }}
      />

      <div
        ref={dotRef}
        className="studio91-custom-cursor-dot"
        style={{
          position: "fixed",
          left: 0,
          top: 0,
          width: dotSize,
          height: dotSize,
          borderRadius: 0,
          backgroundColor: orange,
          transition: "width 0.18s ease, height 0.18s ease, opacity 0.2s ease",
          pointerEvents: "none",
          zIndex: 10000,
          opacity: visible ? 1 : 0.95,
          marginLeft: -dotSize / 2,
          marginTop: -dotSize / 2,
          willChange: "transform, width, height, opacity",
        }}
      />
    </>
  );
}
