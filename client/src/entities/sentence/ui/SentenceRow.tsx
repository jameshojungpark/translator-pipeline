import { memo } from "react";

import type { Sentence } from "../model/types";

import "./SentenceRow.css";

/**
 * One caption line: the original-language transcript above its translation.
 * Every line renders at the same size and color; the active line (the one
 * being voiced right now, or the newest) is marked with an indigo rule and
 * a blinking caret.
 */
export const SentenceRow = memo(function SentenceRow({
  sentence,
  active,
}: {
  sentence: Sentence;
  active: boolean;
}) {
  const pending = sentence.translation === null;
  return (
    <div className={`sentence${active ? " active" : ""}`}>
      {sentence.source && <div className="sentence-source">{sentence.source}</div>}
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
