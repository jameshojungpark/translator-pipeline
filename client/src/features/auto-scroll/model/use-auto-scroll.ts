import { useCallback, useLayoutEffect, useState, type RefObject } from "react";

/** Keep a scrollable element pinned to the bottom while enabled. */
export function useAutoScroll(ref: RefObject<HTMLElement | null>, content: unknown) {
  const [enabled, setEnabled] = useState(true);

  useLayoutEffect(() => {
    if (enabled && ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [enabled, content, ref]);

  const toggle = useCallback(() => setEnabled((value) => !value), []);
  return { enabled, toggle };
}
