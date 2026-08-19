export default function LiveBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-live/40 bg-live/10 px-2 py-0.5 text-[10px] font-bold tracking-wide text-live">
      <span className="h-1.5 w-1.5 rounded-full bg-live animate-pulse-glow" />
      LIVE
    </span>
  );
}
