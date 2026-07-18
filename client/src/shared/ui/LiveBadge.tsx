import "./LiveBadge.css";

/** On-air pill: pulsing red LIVE while connected, muted while reconnecting. */
export function LiveBadge({ on }: { on: boolean }) {
  return (
    <span className={`live-badge${on ? "" : " off"}`} role="status">
      <i className="live-badge-dot" />
      {on ? "LIVE" : "OFF AIR"}
    </span>
  );
}
