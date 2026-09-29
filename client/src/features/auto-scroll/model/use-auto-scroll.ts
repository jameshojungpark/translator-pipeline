import { useCallback, useEffect, useLayoutEffect, useRef, useState, type RefObject } from "react";

/**
 * Keep a scrollable element pinned to the bottom while enabled.
 *
 * The on/off toggle is the source of truth. While on, scrolling up pauses
 * following (so the reader can look back) and scrolling back to the bottom
 * resumes it. Once the reader explicitly turns it off, it stays off until
 * they turn it back on — reaching the bottom by hand does not re-enable it.
 */
export function useAutoScroll(ref: RefObject<HTMLElement | null>, content: unknown) {
  const [enabled, setEnabled] = useState(true);
  const switchedOff = useRef(false);

  useLayoutEffect(() => {
    if (enabled && ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [enabled, content, ref]);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const onScroll = () => {
      if (switchedOff.current) return;
      setEnabled(el.scrollHeight - el.scrollTop - el.clientHeight < 40);
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [ref]);

  const toggle = useCallback(() => {
    setEnabled((value) => {
      switchedOff.current = value;
      return !value;
    });
  }, []);
  return { enabled, toggle };
}
