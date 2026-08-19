"use client";

import { useEffect, useRef, useState } from "react";

export interface PaletteItem {
  label: string;
  group: string;
  targetId: string;
}

export default function CommandPalette({ items }: { items: PaletteItem[] }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (open) {
      setQuery("");
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  const filtered = items.filter((i) => i.label.toLowerCase().includes(query.toLowerCase()));

  function jumpTo(id: string) {
    setOpen(false);
    const el = document.getElementById(id);
    if (!el) return;
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.classList.add("ring-2", "ring-live");
    setTimeout(() => el.classList.remove("ring-2", "ring-live"), 1200);
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 pt-24"
      onClick={() => setOpen(false)}
    >
      <div
        className="w-full max-w-md rounded-lg border border-border bg-card shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Jump to a pair or metric…"
          className="w-full rounded-t-lg bg-transparent px-4 py-3 text-sm text-zinc-100 outline-none placeholder:text-muted"
        />
        <div className="max-h-72 overflow-y-auto border-t border-border">
          {filtered.length === 0 && (
            <div className="px-4 py-3 text-xs text-muted">No matches</div>
          )}
          {filtered.map((item) => (
            <button
              key={item.targetId + item.label}
              onClick={() => jumpTo(item.targetId)}
              className="flex w-full items-center justify-between px-4 py-2 text-left text-sm text-zinc-200 hover:bg-white/5"
            >
              <span>{item.label}</span>
              <span className="text-[10px] text-muted">{item.group}</span>
            </button>
          ))}
        </div>
        <div className="border-t border-border px-4 py-1.5 text-[10px] text-muted">
          ⌘K to toggle · Esc to close
        </div>
      </div>
    </div>
  );
}
