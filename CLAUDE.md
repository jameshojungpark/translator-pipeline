# Live Sermon Translator — Gemini Live API version

## What this project is

A real-time speech translation system for live sermons (English → Korean) with three parts:

1. **Host app** — captures the preacher's microphone and streams audio to the server. The host is the ONLY audio input in the system.
2. **Server** — relays host audio into a Gemini Live API session configured as a simultaneous interpreter (system instruction with glossary + style rules), and broadcasts Gemini's output (translated audio, input transcript, output transcript) to all clients in the session.
3. **Client app** — passive receiver. Displays the English transcript and Korean translation, plays the translated audio. Clients NEVER open a microphone or send audio.

Read `SPEC.md` fully before writing any code. This is a RELAY architecture — there is no STT stage, no sentence buffer, no chunk aggregator, and no separate translation call. Gemini Live does speech-to-speech in one session.

## Tech stack

- **Server:** Python 3.11+, FastAPI, uvicorn, `google-genai` SDK (Live API), python-dotenv
- **Frontend (client viewer):** React + TypeScript + Vite, organized by Feature-Sliced Design (`client/src` — layers `app/pages/features/entities/shared`; layer rules enforced by Steiger). Web Audio playback lives in `client/src/shared/lib/audio` as imperative modules — do not move scheduling into React state.
- **Frontend (host):** plain HTML/JS at `client/public/host.html` (served verbatim; not yet migrated to React). AudioWorklet capture/downsampling to 16 kHz.
- The server serves the built frontend from `client/dist` — run `npm run build` in `client/` after frontend changes (or use `npm run dev` for the Vite dev server, which proxies `/ws` to uvicorn on port 8000).
- **Transport:** WebSockets (host→server audio, server→clients results)
- **Config:** `.env` with `GEMINI_API_KEY` (already present — load it, never hardcode, never log it)

## Architecture rules (do not violate)

- Use a general Live API model that supports `system_instruction` and native audio (see SPEC §2 for model selection). Do NOT use `gemini-3.5-live-translate-preview` — its translation mode does not support instructions, and this project requires a glossary.
- The system instruction (interpreter role + style rules + glossary) is built server-side from `server/glossary.py` and injected at session creation. Clients and host never see or set it.
- The Gemini API key stays server-side only. The host and client apps talk only to our server.
- One host per room/session, N passive clients. Client sockets are receive-only.
- Audio in to Gemini: raw little-endian 16-bit PCM, 16 kHz mono, ~100 ms chunks. Audio out from Gemini: 24 kHz 16-bit PCM mono. The host frontend is responsible for downsampling mic capture to 16 kHz; the server does not transcode.
- Handle Gemini session lifetime: on `GoAway`, pre-open a replacement session and switch the uplink without dropping audio (SPEC §6).
- All Gemini output relays to clients as it streams — do not buffer waiting for complete turns.

## Code style

- Type hints everywhere on the server. Small modules:
  `server/main.py` (routes), `server/rooms.py`, `server/gemini_session.py` (session wrapper + lifecycle), `server/glossary.py` (glossary dict + style rules + instruction builder)
- pytest for pure logic (instruction builder, room broadcast). The Gemini session wrapper gets tested against a fake session object, not the live API.
- Log session lifecycle events (opened, GoAway received, swapped, closed) and relay counts per session id.

## Commands

- Run server: `uvicorn server.main:app --reload`
- Tests: `pytest`
- Lint: `ruff check .`
- Client (from `client/`): `npm run dev` (Vite dev server), `npm run build` (type-check + build to `client/dist`), `npm run lint:fsd` (Steiger FSD layer lint)
