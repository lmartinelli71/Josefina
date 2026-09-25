# Josefina

**Real-time translated captions for live events.**

Josefina is an open-source platform for conferences, talks, classrooms, and live events where part of the audience needs subtitles in another language.

A producer creates and manages live sessions, a speaker transmits microphone audio from the browser, and viewers receive translated captions through a simple web link — without installing an application.

Built during the **Nerdearla Vibeathon 2026**.

---

## Why Josefina

Live events increasingly reach multilingual audiences, but simultaneous interpretation is difficult and expensive to scale across many rooms, speakers, and sessions.

Josefina explores a lightweight alternative:

1. A producer creates a live session.
2. The speaker opens the producer interface and starts the microphone.
3. Audio is streamed continuously to the backend.
4. The speech engine processes and translates the audio.
5. Viewers open a session URL and receive translated captions in real time.

The goal is not to replace professional interpreters in every context. The goal is to make multilingual accessibility easier to deploy and operate for live events.

---

## Current MVP

The current prototype supports:

- multiple independent conference sessions;
- browser microphone capture;
- WebM/Opus audio streaming through WebSockets;
- continuous FFmpeg conversion to PCM 16 kHz mono;
- asynchronous per-session audio queues;
- live speech processing with Gemini;
- English-to-Spanish live translation;
- translated captions delivered through WebSockets;
- independent viewer links for every session;
- multiple viewers per session;
- a production dashboard;
- live producer/session status;
- remote session shutdown from the production console.

Viewers only need a browser and the session link.

---

## Demo flow

A typical demo looks like this:

1. Open the production dashboard.
2. Create a new session.
3. Open the producer interface.
4. Copy the viewer link.
5. Open the viewer page in another browser tab or device.
6. Start the microphone.
7. Speak in English.
8. Spanish captions appear live for connected viewers.
9. Return to the production dashboard.
10. Close the session when the talk finishes.

---

## Architecture

Josefina uses a lightweight **Hexagonal Architecture**, also known as **Ports and Adapters**.

The purpose of this design is not architectural complexity for its own sake. It keeps the core streaming and session-management logic independent from external technologies such as Gemini, WebSockets, FastAPI, FFmpeg, or the browser.

```text
backend/
├── domain/
├── application/
├── ports/
├── adapters/
└── main.py
```

### Domain

The domain contains the core business concepts of Josefina.

Examples:

- `ConferenceSession`
- `CaptionSegment`

These objects represent session and caption behavior without depending on FastAPI, Gemini, WebSockets, or infrastructure code.

### Application

The application layer coordinates the use cases and runtime behavior.

Examples:

- `SessionManager`
- `StreamingOrchestrator`
- per-session runtimes
- asynchronous audio queues

This layer coordinates how sessions are created, started, stopped, and processed.

### Ports

Ports define the contracts that the application expects from external services.

Examples:

- `SpeechEngine`
- `CaptionPublisher`

The application depends on these abstractions rather than directly on a specific provider.

For example, the streaming orchestrator depends on `SpeechEngine`, not on Gemini-specific implementation details.

### Adapters

Adapters connect the application to external technologies.

Current examples include:

- `GeminiAdapter`
- `WebSocketCaptionPublisher`
- FastAPI HTTP endpoints
- audio WebSocket input

This means a different speech provider could implement the same port without requiring changes to the core orchestration flow.

```text
                    ┌────────────────────┐
                    │       Domain       │
                    │                    │
                    │ ConferenceSession  │
                    │ CaptionSegment     │
                    └─────────▲──────────┘
                              │
                    ┌─────────┴──────────┐
                    │    Application     │
                    │                    │
                    │  SessionManager    │
                    │  Orchestrator      │
                    └─────────▲──────────┘
                              │
                    ┌─────────┴──────────┐
                    │       Ports        │
                    │                    │
                    │  SpeechEngine      │
                    │ CaptionPublisher   │
                    └─────────▲──────────┘
                              │
              ┌───────────────┴────────────────┐
              │                                │
     ┌────────┴────────┐              ┌────────┴──────────┐
     │ Gemini Adapter  │              │ WebSocket Adapter │
     └─────────────────┘              └───────────────────┘
```

---

## Real-time streaming flow

The live path is:

```text
Speaker microphone
        |
        v
Browser MediaRecorder
        |
        v
WebM / Opus chunks
        |
        v
Audio WebSocket
        |
        v
FastAPI backend
        |
        v
FFmpeg
WebM / Opus -> PCM 16 kHz mono
        |
        v
Per-session audio queue
        |
        v
StreamingOrchestrator
        |
        v
SpeechEngine port
        |
        v
GeminiAdapter
        |
        v
CaptionAssembler
        |
        v
CaptionPublisher port
        |
        v
WebSocketCaptionPublisher
        |
        v
Viewer browser
```

Audio is sent incrementally rather than waiting for a complete recording to finish.

That is the key design decision behind the low-latency experience.

---

## Multi-session model

Each live conference session owns an independent runtime.

```text
Session A
├── runtime
├── audio queue
├── speech connection
└── viewers

Session B
├── runtime
├── audio queue
├── speech connection
└── viewers

Session C
├── runtime
├── audio queue
├── speech connection
└── viewers
```

This isolates live sessions at the application level and provides a clear path toward horizontal scaling.

The current hackathon MVP runs on a single backend process and has not been load-tested at large scale, so no specific concurrency limit is claimed.

---

## Frontend

The frontend separates production and audience responsibilities.

### Production dashboard

```text
/producer
```

The producer can:

- create sessions;
- see existing sessions;
- see whether a producer is connected;
- see viewer counts;
- open producer interfaces;
- open viewer interfaces;
- close sessions.

### Producer session

```text
/session/<session_id>/producer
```

The producer can:

- start and stop microphone capture;
- see live captions;
- copy the viewer link;
- close the session.

### Viewer session

```text
/session/<session_id>/viewer
```

The audience receives translated captions without access to production controls.

---

## Technology stack

### Backend

- Python
- FastAPI
- asyncio
- WebSockets
- FFmpeg
- Gemini Live API

### Frontend

- Next.js
- React
- TypeScript
- MediaRecorder API
- WebSockets
- Tailwind CSS

---

## Requirements

Before running Josefina locally, install:

- Python 3
- Node.js
- npm
- FFmpeg
- a Gemini API key

Check FFmpeg:

```bash
ffmpeg -version
```

---

## Environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

**Never commit `.env` or API keys to the repository.**

A recommended `.gitignore` includes:

```gitignore
.env
.venv/
node_modules/
.next/
__pycache__/
*.pyc
```

---

## Running the backend

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies used by the project.

If the repository contains `requirements.txt`:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

---

## Running the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:3000/producer
```

---

## API overview

The current MVP exposes session-management endpoints such as:

```text
POST   /sessions
GET    /sessions
GET    /sessions/{session_id}
DELETE /sessions/{session_id}
```

Real-time communication uses separate WebSockets for audio and captions:

```text
/ws/audio/{session_id}
/ws/captions/{session_id}
```

This keeps producer audio transport separate from viewer caption delivery.

---

## Quality

Josefina processes continuous live speech instead of waiting for complete prerecorded files.

Translation quality depends on factors such as:

- microphone quality;
- background noise;
- speaker pronunciation;
- network conditions;
- speech model performance;
- technical vocabulary.

For the Vibeathon demo, the system is tested with both normal speech and technical terminology.

---

## Latency

The application is designed around streaming.

```text
microphone
-> 500 ms WebM/Opus chunks
-> WebSocket
-> FFmpeg
-> PCM
-> Gemini Live
-> caption assembly
-> WebSocket
-> viewer
```

The system does not wait for an entire talk or recording to finish before generating captions.

---

## Scalability

The MVP currently runs on a single backend instance, but the session model is isolated by design.

Each active session has its own:

- runtime;
- audio queue;
- producer state;
- speech connection;
- viewer group.

Creating another conference session does not require changing the processing architecture.

A production evolution could distribute independent sessions across multiple backend workers or machines and move shared session state to infrastructure such as Redis.

---

## Deployment

The hackathon version runs the backend and frontend as separate local processes.

This was an intentional decision to prioritize a stable, working, low-latency end-to-end flow during the Vibeathon.

A production version could add:

- Docker;
- Docker Compose;
- a reverse proxy;
- persistent session state;
- multiple backend instances;
- centralized observability.

A possible production topology is:

```text
Internet
   |
   v
Reverse Proxy
   |
   +------> Next.js frontend
   |
   +------> FastAPI instances
                |
                +--> Session A
                +--> Session B
                +--> Session C
```

---

## Innovation

Josefina is not only a speech-to-text demo.

The MVP models a real event-production workflow:

- a producer creates and manages multiple live sessions;
- every session has an independent speaker/audio path;
- viewers receive a shareable link;
- audience users do not need an account or installation;
- production and audience interfaces are separated;
- sessions can be centrally closed from the production console.

The focus is on making real-time multilingual captions operationally useful during an event.

---

## Current limitations

This is a hackathon MVP.

Current limitations include:

- English-to-Spanish is the primary configured translation path;
- session state is stored in memory;
- sessions are lost when the backend restarts;
- there is no persistent database yet;
- there is no authentication yet;
- there is no distributed session registry yet;
- the project has not been load-tested at production scale;
- Docker deployment is not part of the current MVP.

These choices were intentional to prioritize the complete real-time user flow during the Vibeathon.

---

## What's next

Possible next steps include:

- additional source and target languages;
- automatic language detection;
- persistent session storage;
- Redis-based distributed session state;
- horizontal backend scaling;
- Docker and Docker Compose deployment;
- producer authentication;
- event and room management;
- downloadable transcripts;
- caption history;
- accessibility customization;
- domain glossaries for technical events;
- latency and quality metrics;
- production observability.

---

## Built for Nerdearla Vibeathon 2026

Josefina was created during the **Nerdearla Vibeathon 2026**.

The project explores how streaming architecture, browser-native audio capture, and modern speech models can make multilingual live events more accessible.

---

## License

This project is released under the **MIT License**.

Copyright (c) 2026 Leonardo Martinelli

See the `LICENSE` file for details.
