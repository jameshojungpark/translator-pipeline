import { useCallback, useState } from "react";

import { DEFAULT_LANG, isLangCode, type LangCode } from "@/shared/config";

/** Viewer language, initialized from and mirrored to the ?lang= URL param. */
export function useLangParam(): [LangCode, (code: LangCode) => void] {
  const [lang, setLang] = useState<LangCode>(() => {
    const fromUrl = new URLSearchParams(location.search).get("lang");
    return isLangCode(fromUrl) ? fromUrl : DEFAULT_LANG;
  });

  const change = useCallback((code: LangCode) => {
    const params = new URLSearchParams(location.search);
    params.set("lang", code);
    history.replaceState(null, "", `?${params.toString()}`);
    setLang(code);
  }, []);

  return [lang, change];
}
