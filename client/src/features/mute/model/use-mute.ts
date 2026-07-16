import { useCallback, useState } from "react";

import type { PlaybackQueue } from "@/shared/lib/audio";

export function useMute(queue: PlaybackQueue) {
  const [muted, setMuted] = useState(false);

  const toggle = useCallback(() => {
    if (queue.enabled && !queue.running) {
      // context died while we were away — this click is a user gesture, so
      // use it to recover instead of toggling mute
      void queue.resume();
      queue.setMuted(false);
      setMuted(false);
      return;
    }
    setMuted((current) => {
      queue.setMuted(!current);
      return !current;
    });
  }, [queue]);

  return { muted, toggle };
}
