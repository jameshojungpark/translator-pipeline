import { useEffect, useMemo, useReducer, useRef, useState } from "react";

import { feedReducer, SentenceRow } from "@/entities/sentence";
import { AutoScrollButton, useAutoScroll } from "@/features/auto-scroll";
import { LangOverlay, LangSelect, useLangParam } from "@/features/language-select";
import { MuteButton, useMute } from "@/features/mute";
import { openRoomSocket } from "@/shared/api";
import { LANGS, type LangCode } from "@/shared/config";
import { PlaybackQueue } from "@/shared/lib/audio";
import { StatusDot } from "@/shared/ui";

import "./ViewerPage.css";

export function ViewerPage() {
  const room = useMemo(() => new URLSearchParams(location.search).get("room") ?? "main", []);
  const [lang, setLang] = useLangParam();
  const [connected, setConnected] = useState(false);
  const [statusText, setStatusText] = useState("connecting…");
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [sentences, dispatch] = useReducer(feedReducer, []);
  const [queue] = useState(() => new PlaybackQueue());
  const { muted, toggle: toggleMute } = useMute(queue);
  const feedRef = useRef<HTMLDivElement>(null);
  const autoScroll = useAutoScroll(feedRef, sentences);

  // Language switch reconnects the socket with the new lang and clears the
  // feed (old entries would be in the wrong language). No page reload, so an
  // already-enabled AudioContext keeps working.
  useEffect(() => {
    dispatch({ type: "clear" });
    const socket = openRoomSocket(room, lang, {
      onStatus: (isConnected) => {
        setConnected(isConnected);
        setStatusText(isConnected ? `room: ${room} · ${LANGS[lang].en}` : "reconnecting…");
      },
      onMessage: (m) => {
        if (m.type === "transcript") {
          dispatch({ type: "transcript", id: m.id, text: m.text });
        } else if (m.type === "translation") {
          dispatch({
            type: "translation",
            id: m.id,
            source: m.source,
            text: m.text,
            reference: m.reference,
          });
        } else if (m.type === "tts") {
          // highlight the matching entry while its audio plays
          queue.enqueue(m.audio, m.rate, {
            onStart: () => dispatch({ type: "speaking", id: m.id, speaking: true }),
            onEnd: () => dispatch({ type: "speaking", id: m.id, speaking: false }),
          });
        }
      },
    });
    return () => socket.close();
  }, [room, lang, queue]);

  // After a browser sleep / audio interruption, recover the AudioContext as
  // soon as the tab is visible again.
  useEffect(() => {
    const onVisibilityChange = () => {
      if (!document.hidden && !muted) void queue.resume();
    };
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => document.removeEventListener("visibilitychange", onVisibilityChange);
  }, [muted, queue]);

  const chooseLangAndEnableAudio = (code: LangCode) => {
    queue.enable(); // must happen inside the click gesture
    setAudioEnabled(true);
    setLang(code);
  };

  return (
    <div className="viewer">
      <header className="viewer-header">
        <h1>Live Sermon Translation</h1>
        <div className="viewer-status">
          <StatusDot on={connected} />
          <span>{statusText}</span>
        </div>
        <LangSelect value={lang} onChange={setLang} />
        <AutoScrollButton enabled={autoScroll.enabled} onToggle={autoScroll.toggle} />
        {audioEnabled && <MuteButton muted={muted} onToggle={toggleMute} />}
      </header>
      <div className="viewer-feed" ref={feedRef}>
        {sentences.map((sentence, index) => (
          <SentenceRow key={index} sentence={sentence} />
        ))}
      </div>
      {!audioEnabled && <LangOverlay onSelect={chooseLangAndEnableAudio} />}
    </div>
  );
}
