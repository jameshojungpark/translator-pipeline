import "./AutoScrollButton.css";

export function AutoScrollButton({ enabled, onToggle }: { enabled: boolean; onToggle: () => void }) {
  return (
    <button
      className={`auto-scroll-btn${enabled ? "" : " off"}`}
      title="Toggle auto-scroll"
      onClick={onToggle}
    >
      {enabled ? "⬇ Auto Scroll" : "⬇ Auto Scroll Off"}
    </button>
  );
}
