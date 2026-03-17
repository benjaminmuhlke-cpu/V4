"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";

interface CursorProps {
  size?: number;
  /** Accent color for the cursor outline (defaults to site orange). */
  accentColor?: string;
  /** Color used when hovering interactive elements (buttons/links). */
  interactiveColor?: string;
}

export const Cursor: React.FC<CursorProps> = ({
  size = 60,
  accentColor = "#ff642b",
  interactiveColor = "#ffffff",
}) => {
  const cursorRef = useRef<HTMLDivElement>(null);
  const requestRef = useRef<number>();
  const previousPos = useRef({ x: -size, y: -size }); // start off-screen

  const [visible, setVisible] = useState(false);
  const [position, setPosition] = useState({ x: -size, y: -size });
  const [isInteractiveHover, setIsInteractiveHover] = useState(false);

  const animate = useCallback(() => {
    if (!cursorRef.current) return;

    const currentX = previousPos.current.x;
    const currentY = previousPos.current.y;
    const targetX = position.x - size / 2;
    const targetY = position.y - size / 2;

    const deltaX = (targetX - currentX) * 0.2;
    const deltaY = (targetY - currentY) * 0.2;

    const newX = currentX + deltaX;
    const newY = currentY + deltaY;

    previousPos.current = { x: newX, y: newY };
    cursorRef.current.style.transform = `translate(${newX}px, ${newY}px)`;

    requestRef.current = requestAnimationFrame(animate);
  }, [position.x, position.y, size]);

  useEffect(() => {
    const supportsHover =
      typeof window !== "undefined" &&
      window.matchMedia?.("(hover: hover) and (pointer: fine)")?.matches;

    if (!supportsHover) return;

    const prefersReducedMotion =
      window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;

    const isInteractiveElement = (element: Element | null) => {
      if (!element) return false;
      const interactive = element.closest(
        'button, a, input, textarea, select, [role="button"], [data-cursor="interactive"]',
      );
      if (!interactive) return false;
      const disabled =
        (interactive as HTMLButtonElement).hasAttribute?.("disabled") ||
        interactive.getAttribute?.("aria-disabled") === "true";
      return !disabled;
    };

    const handleMouseMove = (e: MouseEvent) => {
      setVisible(true);
      setPosition({ x: e.clientX, y: e.clientY });

      const hovered = document.elementFromPoint(e.clientX, e.clientY);
      setIsInteractiveHover(isInteractiveElement(hovered));
    };

    const handleMouseEnter = () => setVisible(true);
    const handleMouseLeave = () => {
      setVisible(false);
      setIsInteractiveHover(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.documentElement.addEventListener("mouseenter", handleMouseEnter);
    document.documentElement.addEventListener("mouseleave", handleMouseLeave);

    const html = document.documentElement;
    const previousAttr = html.getAttribute("data-custom-cursor");
    html.setAttribute("data-custom-cursor", "true");

    if (!prefersReducedMotion) {
      requestRef.current = requestAnimationFrame(animate);
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.documentElement.removeEventListener(
        "mouseenter",
        handleMouseEnter,
      );
      document.documentElement.removeEventListener(
        "mouseleave",
        handleMouseLeave,
      );
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
      if (previousAttr === null) html.removeAttribute("data-custom-cursor");
      else html.setAttribute("data-custom-cursor", previousAttr);
    };
  }, [animate]);

  return (
    <div
      ref={cursorRef}
      className="fixed relative pointer-events-none z-50 transition-opacity duration-300"
      style={{
        width: size,
        height: size,
        opacity: visible ? 1 : 0,
      }}
      aria-hidden="true"
    >
      {/* Outer ring: always orange (no blend) to avoid turning blue on orange backgrounds */}
      <div
        className="absolute inset-0 rounded-full"
        style={{
          border: `2px solid ${isInteractiveHover ? interactiveColor : accentColor}`,
        }}
      />

      {/* Inner fill: invert underlying colors for white-on-black text effect */}
      <div
        className="absolute inset-1 rounded-full"
        style={{
          background: isInteractiveHover ? accentColor : "#ffffff",
          mixBlendMode: isInteractiveHover ? "normal" : ("difference" as const),
        }}
      />
    </div>
  );
};

export default Cursor;
