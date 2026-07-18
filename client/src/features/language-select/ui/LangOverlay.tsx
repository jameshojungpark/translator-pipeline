import { LANG_CODES, LANGS, type LangCode } from "@/shared/config";

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
        <h2>Live Sermon Translation</h2>
        <p>Choose your language. Subtitles and audio start right away — change it anytime from the top menu.</p>
        <div className="lang-overlay-grid">
          {LANG_CODES.map((code) => {
            const meta = LANGS[code];
            return (
              <button key={code} className="lang-overlay-btn" onClick={() => onSelect(code)}>
                <span className="lang-overlay-native">{meta.label}</span>
                {meta.en !== meta.label && <span className="lang-overlay-gloss">{meta.en}</span>}
                {meta.textOnly && <span className="lang-overlay-note">Subtitles only</span>}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
