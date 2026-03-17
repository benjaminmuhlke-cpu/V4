"use client";

import { Cursor } from "@/components/ui/inverted-cursor";

export default function CursorDemoPage() {
  return (
    <div className="relative w-full h-screen overflow-hidden cursor-none">
      <Cursor />

      <main className="flex items-center justify-center h-full">
        <h1 className="text-4xl font-extrabold select-none">Move your mouse</h1>
      </main>
    </div>
  );
}

