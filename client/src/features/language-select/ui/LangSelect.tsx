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
      <span className="lang-pill-chip">
        Change
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </span>
      <select
        className="lang-pill-select"
        title="Language"
        aria-label="Translation language"
        value={value}
        onChange={(event) => onChange(event.target.value as LangCode)}
      >
        {LANG_CODES.map((code) => (
          <option key={code} value={code}>
            {langLabel(LANGS[code])}
          </option>
        ))}
      </select>
    </div>
  );
}
