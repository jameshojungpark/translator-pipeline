import { useState } from "react";
import { LANG_CODES, LANGS, langLabel, type LangCode } from "@/shared/config";

import "./LangSelect.css";

/**
 * "Translating to" pill. A transparent native <select> covers the whole
 * card, so tapping anywhere opens the platform language picker.
 */
export function LangSelect({
  value,
  onChange,
}: {
  value: LangCode;
  onChange: (code: LangCode) => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="lang-pill">
      <span className="lang-pill-icon" aria-hidden="true">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
          <circle cx="12" cy="12" r="9" />
          <path d="M3 12h18" />
          <path d="M12 3a13.5 13.5 0 0 1 0 18a13.5 13.5 0 0 1 0-18Z" />
        </svg>
      </span>
      <span className="lang-pill-labels">
        <span className="lang-pill-overline">Translating to</span>
        <span className="lang-pill-value">{LANGS[value].label}</span>
      </span>
      <button
        type="button"
        className="lang-pill-chip"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        Change
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      {open && (
        <ul className="lang-menu" role="listbox">
          {LANG_CODES.map((code) => (
            <li
              key={code}
              role="option"
              aria-selected={code === value}
              className={`lang-menu-item ${code === value ? "is-selected" : ""}`}
              onClick={() => { onChange(code); setOpen(false); }}
            >
              {langLabel(LANGS[code])}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
