import "./MuteButton.css";

export function MuteButton({ muted, onToggle }: { muted: boolean; onToggle: () => void }) {
  return (
    <button
      className="mute-btn"
      title={muted ? "Unmute" : "Mute"}
      aria-pressed={muted}
      onClick={onToggle}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M11 5 6 9H2v6h4l5 4V5Z" fill="currentColor" stroke="none" />
        {muted ? (
          <path d="m16 9 6 6m0-6-6 6" />
        ) : (
          <>
            <path d="M15.5 8.5a5 5 0 0 1 0 7" />
            <path d="M18.5 5.5a9.5 9.5 0 0 1 0 13" />
          </>
        )}
      </svg>
    </button>
  );
}
