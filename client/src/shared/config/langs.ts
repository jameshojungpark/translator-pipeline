export interface LangMeta {
  en: string;
  label: string;
  textOnly?: boolean;
}

export type LangCode = "en" | "ko" | "zh" | "yue" | "pa" | "es" | "fr" | "fa";

// Language menu (English names first — the picker itself is explained in
// English). textOnly languages have no Cloud TTS voice: subtitles, no audio.
// Keep textOnly languages at the bottom so audio-capable ones list first.
export const LANGS: Record<LangCode, LangMeta> = {
  en: { en: "English", label: "English" },
  ko: { en: "Korean", label: "한국어" },
  zh: { en: "Mandarin", label: "普通话" },
  yue: { en: "Cantonese", label: "廣東話" },
  pa: { en: "Punjabi", label: "ਪੰਜਾਬੀ" },
  es: { en: "Spanish", label: "Español" },
  fr: { en: "French", label: "Français" },
  fa: { en: "Farsi", label: "فارسی", textOnly: true },
};

export const LANG_CODES = Object.keys(LANGS) as LangCode[];

export const DEFAULT_LANG: LangCode = "ko";

export function isLangCode(code: string | null): code is LangCode {
  return code !== null && code in LANGS;
}

export function langLabel(meta: LangMeta): string {
  return meta.en === meta.label ? meta.en : `${meta.en} · ${meta.label}`;
}
