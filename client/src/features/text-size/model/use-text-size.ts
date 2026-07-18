import { useCallback, useState } from "react";

export type TextSize = "small" | "medium" | "large";

const STORAGE_KEY = "woaf-text-size";

/** Caption text size, remembered across visits. */
export function useTextSize(): [TextSize, (size: TextSize) => void] {
  const [size, setSize] = useState<TextSize>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved === "small" || saved === "large" ? saved : "medium";
  });

  const change = useCallback((next: TextSize) => {
    localStorage.setItem(STORAGE_KEY, next);
    setSize(next);
  }, []);

  return [size, change];
}
