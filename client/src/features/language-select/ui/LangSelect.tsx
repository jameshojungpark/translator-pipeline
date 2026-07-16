import { LANG_CODES, LANGS, langLabel, type LangCode } from "@/shared/config";

import "./LangSelect.css";

export function LangSelect({
  value,
  onChange,
}: {
  value: LangCode;
  onChange: (code: LangCode) => void;
}) {
  return (
    <select
      className="lang-select"
      title="Language"
      value={value}
      onChange={(event) => onChange(event.target.value as LangCode)}
    >
      {LANG_CODES.map((code) => (
        <option key={code} value={code}>
          {langLabel(LANGS[code])}
        </option>
      ))}
    </select>
  );
}
