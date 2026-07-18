export type SentenceId = string | number;

export interface TranscriptMessage {
  type: "transcript";
  id: SentenceId;
  text: string;
}

export interface TranslationMessage {
  type: "translation";
  id: SentenceId;
  source: string;
  text: string;
  reference?: string;
  lang?: string;
}

export interface TtsMessage {
  type: "tts";
  id: SentenceId;
  audio: string; // base64 16-bit PCM
  rate?: number;
}

export interface StatsMessage {
  type: "stats";
  total: number;
  langs: Record<string, number>;
  host: boolean; // a host is currently broadcasting
}

export type ServerMessage =
  | TranscriptMessage
  | TranslationMessage
  | TtsMessage
  | StatsMessage;
