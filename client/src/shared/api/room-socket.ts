import type { ServerMessage } from "./messages";

export interface RoomSocketHandlers {
  onMessage: (message: ServerMessage) => void;
  onStatus: (connected: boolean) => void;
}

export interface RoomSocket {
  close: () => void;
}

const RECONNECT_DELAY_MS = 2000;

/**
 * Receive-only socket to /ws/client with auto-reconnect. close() detaches the
 * handlers and stops reconnecting, so a superseded socket (e.g. after a
 * language switch) can't clobber its replacement's status.
 */
export function openRoomSocket(
  room: string,
  lang: string,
  handlers: RoomSocketHandlers,
): RoomSocket {
  let ws: WebSocket | null = null;
  let reconnectTimer: number | undefined;
  let closed = false;

  function connect(): void {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${proto}://${location.host}/ws/client?room=${room}&lang=${lang}`);
    ws.onopen = () => handlers.onStatus(true);
    ws.onmessage = (event) => handlers.onMessage(JSON.parse(event.data) as ServerMessage);
    ws.onclose = () => {
      if (closed) return;
      handlers.onStatus(false);
      reconnectTimer = window.setTimeout(connect, RECONNECT_DELAY_MS);
    };
  }

  connect();
  return {
    close() {
      closed = true;
      clearTimeout(reconnectTimer);
      ws?.close();
    },
  };
}
