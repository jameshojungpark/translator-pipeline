import type { SentenceId } from "@/shared/api";

import type { Sentence } from "./types";

export type FeedAction =
  | { type: "transcript"; id: SentenceId; text: string }
  | { type: "translation"; id: SentenceId; source: string; text: string; reference?: string }
  | { type: "speaking"; id: SentenceId; speaking: boolean }
  | { type: "clear" };

// Sentences only ever append, so the latest entry for an id is the live one.
function findById(items: Sentence[], id: SentenceId): number {
  for (let i = items.length - 1; i >= 0; i--) {
    if (items[i].id === id) return i;
  }
  return -1;
}

export function feedReducer(items: Sentence[], action: FeedAction): Sentence[] {
  switch (action.type) {
    case "transcript":
      return [
        ...items,
        { id: action.id, source: action.text, translation: null, reference: "", speaking: false },
      ];
    case "translation": {
      const i = findById(items, action.id);
      // A translation whose transcript never arrived still gets an entry —
      // the message carries its own source text.
      if (i === -1) {
        return [
          ...items,
          {
            id: action.id,
            source: action.source,
            translation: action.text,
            reference: action.reference ?? "",
            speaking: false,
          },
        ];
      }
      const next = items.slice();
      next[i] = {
        ...next[i],
        translation: action.text, // verse quotes arrive embedded, 〔ref〕 around just the verse
        reference: action.reference ?? next[i].reference,
      };
      return next;
    }
    case "speaking": {
      const i = findById(items, action.id);
      if (i === -1) return items;
      const next = items.slice();
      next[i] = { ...next[i], speaking: action.speaking };
      return next;
    }
    case "clear":
      return [];
  }
}
