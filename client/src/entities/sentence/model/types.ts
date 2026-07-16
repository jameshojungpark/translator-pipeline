import type { SentenceId } from "@/shared/api";

export interface Sentence {
  id: SentenceId;
  source: string; // speaker-language transcript
  translation: string | null; // null while pending
  reference: string; // Bible verse reference chip ("" if none)
  speaking: boolean; // its TTS clip is currently playing
}
