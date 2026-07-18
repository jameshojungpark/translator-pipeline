import "./Waveform.css";

/** Five animated equalizer bars; freezes low while not live. */
export function Waveform({ active }: { active: boolean }) {
  return (
    <span className={`waveform${active ? "" : " idle"}`} aria-hidden="true">
      <i /><i /><i /><i /><i />
    </span>
  );
}
