import "./AutoScrollButton.css";

/** Labeled on/off switch in the live bar: follow the live line, or stay put to read back. */
export function AutoScrollButton({ enabled, onToggle }: { enabled: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      role="switch"
      className="auto-scroll-btn"
      title={enabled ? "Turn auto-scroll off" : "Turn auto-scroll on"}
      aria-checked={enabled}
      onClick={onToggle}
    >
      <span className="auto-scroll-label">Auto-scroll</span>
      <span className="auto-scroll-track" aria-hidden="true">
        <span className="auto-scroll-thumb" />
      </span>
    </button>
  );
}
