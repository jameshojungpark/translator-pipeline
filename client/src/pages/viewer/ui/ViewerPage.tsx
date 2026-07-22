import { useEffect, useMemo, useReducer, useRef, useState } from "react";

import { feedReducer, SentenceRow } from "@/entities/sentence";
import { AutoScrollButton, useAutoScroll } from "@/features/auto-scroll";
import { LangOverlay, LangSelect, useLangParam } from "@/features/language-select";
import { MuteButton, useMute } from "@/features/mute";
import { TextSizeControl, useTextSize } from "@/features/text-size";
import { ThemeToggle, useTheme } from "@/features/theme-toggle";
import { openRoomSocket } from "@/shared/api";
import { type LangCode } from "@/shared/config";
import { PlaybackQueue } from "@/shared/lib/audio";
import { LiveBadge } from "@/shared/ui";

import "./ViewerPage.css";

export function ViewerPage() {
  const room = useMemo(() => new URLSearchParams(location.search).get("room") ?? "main", []);
  const [lang, setLang] = useLangParam();
  const [connected, setConnected] = useState(false);
  const [hostLive, setHostLive] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [sentences, dispatch] = useReducer(feedReducer, []);
  const [queue] = useState(() => new PlaybackQueue());
  const { muted, toggle: toggleMute } = useMute(queue);
  const feedRef = useRef<HTMLDivElement>(null);
  const autoScroll = useAutoScroll(feedRef, sentences);
  const [textSize, setTextSize] = useTextSize();
  const [theme, toggleTheme] = useTheme();

  // Language switch reconnects the socket with the new lang and clears the
  // feed (old entries would be in the wrong language). No page reload, so an
  // already-enabled AudioContext keeps working.
  useEffect(() => {
    dispatch({ type: "clear" });
    const socket = openRoomSocket(room, lang, {
      onStatus: (isConnected) => {
        setConnected(isConnected);
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
        } else if (m.type === "stats") {
          setHostLive(m.host);
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

  // LIVE means a host is actually broadcasting, not merely that our socket
  // is open — before the service starts the badge stays off.
  const live = connected && hostLive;

  // The emphasized line: the one whose audio is playing right now, or —
  // between clips / with audio off — simply the newest.
  let activeIndex = sentences.length - 1;
  for (let i = sentences.length - 1; i >= 0; i--) {
    if (sentences[i].speaking) {
      activeIndex = i;
      break;
    }
  }

  return (
    <div className="viewer">
      <header className="viewer-header">
        <div className="viewer-topbar">
          <div className="viewer-brand">
            <span className="viewer-logo" aria-hidden="true">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round">
                <path d="M1.5 5.5v3" />
                <path d="M4.25 3.5v7" />
                <path d="M7 1.5v11" />
                <path d="M9.75 3.5v7" />
                <path d="M12.5 5.5v3" />
              </svg>
            </span>
            <span className="viewer-wordmark">Worship On Air</span>
          </div>
          <div className="viewer-topbar-actions">
            <ThemeToggle theme={theme} onToggle={toggleTheme} />
            <LiveBadge on={live} />
          </div>
        </div>
        <LangSelect value={lang} onChange={setLang} />
      </header>

      <div className="viewer-feed-wrap">
        <div className="viewer-feed-mask" />
        <div className={`viewer-feed size-${textSize}`} ref={feedRef}>
          {sentences.map((sentence, index) => (
            <SentenceRow
              key={index}
              sentence={sentence}
              active={index === activeIndex}
              reading={!autoScroll.enabled}
            />
          ))}
        </div>
      </div>

      <div className="viewer-bottom">
        <div className="live-bar">
          <TextSizeControl value={textSize} onChange={setTextSize} />
          <div className="live-bar-actions">
            <MuteButton muted={muted} onToggle={toggleMute} />
            <AutoScrollButton enabled={autoScroll.enabled} onToggle={autoScroll.toggle} />
          </div>
        </div>
      </div>

      {!audioEnabled && <LangOverlay onSelect={chooseLangAndEnableAudio} />}
    </div>
  );
}
