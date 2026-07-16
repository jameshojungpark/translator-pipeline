import "./MuteButton.css";

export function MuteButton({ muted, onToggle }: { muted: boolean; onToggle: () => void }) {
  return (
    <button className="mute-btn" title="음소거" onClick={onToggle}>
      {muted ? "🔇" : "🔊"}
    </button>
  );
}
