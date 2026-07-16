import { LANG_CODES, LANGS, langLabel, type LangCode } from "@/shared/config";

import "./LangOverlay.css";

/**
 * First-visit language picker. The buttons double as the audio-enable
 * gesture: picking a language is the user click browsers require before
 * audio can play.
 */
export function LangOverlay({ onSelect }: { onSelect: (code: LangCode) => void }) {
  return (
    <div className="lang-overlay">
      <div className="lang-overlay-box">
        <h2>Select your language</h2>
        <p>
          Subtitles and audio will play in the language you choose. You can change it later from
          the menu at the top.
        </p>
        {LANG_CODES.map((code) => {
          const meta = LANGS[code];
          return (
            <button key={code} className="lang-overlay-btn" onClick={() => onSelect(code)}>
              {meta.textOnly ? "💬" : "🔊"} {langLabel(meta)}
              {meta.textOnly && <small>subtitles only — no audio</small>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
