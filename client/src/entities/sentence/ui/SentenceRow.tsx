import { memo } from "react";

import type { Sentence } from "../model/types";

import "./SentenceRow.css";

export const SentenceRow = memo(function SentenceRow({ sentence }: { sentence: Sentence }) {
  const pending = sentence.translation === null;
  return (
    <div className={`sentence${sentence.speaking ? " speaking" : ""}`}>
      <div className="sentence-source">{sentence.source}</div>
      <div className="sentence-target-row">
        {/* dir="auto": Farsi is right-to-left */}
        <div className={`sentence-target${pending ? " pending" : ""}`} dir="auto">
          {pending ? "Translating…" : sentence.translation}
        </div>
        {sentence.reference && <span className="sentence-ref">{sentence.reference}</span>}
      </div>
    </div>
  );
});
