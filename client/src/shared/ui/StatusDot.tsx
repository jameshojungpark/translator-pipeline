import "./StatusDot.css";

export function StatusDot({ on }: { on: boolean }) {
  return <span className={`status-dot${on ? " on" : ""}`} />;
}
