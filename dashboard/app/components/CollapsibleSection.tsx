"use client";

import { useState, type ReactNode } from "react";

export default function CollapsibleSection({
  title,
  defaultOpen = true,
  children,
  id,
}: {
  title: string;
  defaultOpen?: boolean;
  children: ReactNode;
  id?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section id={id} className="scroll-mt-4">
      <button
        onClick={() => setOpen((v) => !v)}
        className="mb-1.5 flex w-full items-center justify-between text-left"
      >
        <h2 className="text-[13px] font-medium text-muted">{title}</h2>
        <span className="text-[10px] text-zinc-600">{open ? "▾" : "▸"}</span>
      </button>
      {open && children}
    </section>
  );
}
