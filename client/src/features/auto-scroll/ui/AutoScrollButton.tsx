import "./AutoScrollButton.css";

/** Pause/resume circle in the live bar: pauses auto-scroll for reading back. */
export function AutoScrollButton({ enabled, onToggle }: { enabled: boolean; onToggle: () => void }) {
  return (
    <button
      className="auto-scroll-btn"
      title={enabled ? "Pause auto-scroll" : "Follow live"}
      aria-pressed={enabled}
      onClick={onToggle}
    >
      {enabled ? (
        <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
          <rect x="2.5" y="0" width="4" height="14" rx="1.5" fill="currentColor" />
          <rect x="8.5" y="0" width="4" height="14" rx="1.5" fill="currentColor" />
        </svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
          <path d="M3.5 1.5 12 7l-8.5 5.5Z" fill="currentColor" />
        </svg>
      )}
    </button>
  );
}
