import { memo } from "react";

import type { Sentence } from "../model/types";

import "./SentenceRow.css";

/**
 * One caption line: the original-language transcript above its translation.
 * The active line (the one being voiced right now, or the newest) is
 * emphasized with an indigo rule and a blinking caret; settled lines fade
 * progressively via CSS. `reading` (feed scrolled back) lifts the fade so
 * past lines are fully legible.
 */
export const SentenceRow = memo(function SentenceRow({
  sentence,
  active,
  reading,
}: {
  sentence: Sentence;
  active: boolean;
  reading: boolean;
}) {
  const pending = sentence.translation === null;
  return (
    <div className={`sentence${active ? " active" : ""}${reading ? " reading" : ""}`}>
      {sentence.source && (
        <div className="sentence-source">
          <svg className="sentence-source-icon" width="12" height="12" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
              strokeLinejoin="round" aria-hidden="true">
            <rect x="9" y="2" width="6" height="11" rx="3" />
            <path d="M5 10a7 7 0 0 0 14 0" />
            <path d="M12 17v4" />
          </svg>
          {sentence.source}
        </div>
      )}
      <div className="sentence-target-row">
        {/* dir="auto": Farsi is right-to-left */}
        <div className="sentence-target" dir="auto">
          {pending ? (
            // language-neutral pending marker — readers may not read English
            <span className="sentence-pending-dots" aria-label="Translating">
              <i /><i /><i />
            </span>
          ) : (
            sentence.translation
          )}
          {active && !pending && <span className="sentence-caret" aria-hidden="true" />}
        </div>
        {sentence.reference && <span className="sentence-ref">{sentence.reference}</span>}
      </div>
    </div>
  );
});
