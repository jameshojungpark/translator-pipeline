import { useCallback, useEffect, useLayoutEffect, useState, type RefObject } from "react";

/**
 * Keep a scrollable element pinned to the bottom while enabled.
 * Scrolling up pauses following (so the reader can look back);
 * scrolling back to the bottom resumes it.
 */
export function useAutoScroll(ref: RefObject<HTMLElement | null>, content: unknown) {
  const [enabled, setEnabled] = useState(true);

  useLayoutEffect(() => {
    if (enabled && ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [enabled, content, ref]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const onScroll = () => {
      setEnabled(el.scrollHeight - el.scrollTop - el.clientHeight < 40);
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [ref]);

  const toggle = useCallback(() => setEnabled((value) => !value), []);
  return { enabled, toggle };
}
