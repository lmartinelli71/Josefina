**# Josefina**

**\*\*Real-time translated captions for live events.\*\***

Josefina is an open-source platform for conferences, talks, classrooms, and live events where part of the audience needs subtitles in another language.

A producer creates and manages live sessions, a speaker transmits microphone audio from the browser, and viewers receive translated captions through a simple web link — without installing an application.

Built during the **\*\*Nerdearla Vibeathon 2026\*\***.

\---

**## Why Josefina**

Live events increasingly reach multilingual audiences, but simultaneous interpretation is difficult and expensive to scale across many rooms, speakers, and sessions.

Josefina explores a lightweight alternative:

1\. A producer creates a live session.

2\. The speaker opens the producer interface and starts the microphone.

3\. Audio is streamed continuously to the backend.

4\. The speech engine processes and translates the audio.

5\. Viewers open a session URL and receive translated captions in real time.

The goal is not to replace professional interpreters in every context. The goal is to make multilingual accessibility easier to deploy and operate for live events.

\---

**## Current MVP**

The current prototype supports:

\- multiple independent conference sessions;

\- browser microphone capture;

\- WebM/Opus audio streaming through WebSockets;

\- continuous FFmpeg conversion to PCM 16 kHz mono;

\- asynchronous per-session audio queues;

\- live speech processing with Gemini;

\- English-to-Spanish live translation;

\- translated captions delivered through WebSockets;

\- independent viewer links for every session;

\- multiple viewers per session;

\- a production dashboard;

\- live producer/session status;

\- remote session shutdown from the production console;

\- containerized frontend and backend;

\- one-command local deployment with Docker Compose.

Viewers only need a browser and the session link.

\---

**## Demo flow**

A typical demo looks like this:

1\. Open the production dashboard.

2\. Create a new session.

3\. Open the producer interface.

4\. Copy the viewer link.

5\. Open the viewer page in another browser tab or device.

6\. Start the microphone.

7\. Speak in English.

8\. Spanish captions appear live for connected viewers.

9\. Return to the production dashboard.

10\. Close the session when the talk finishes.

\---

**## Architecture**

Josefina uses a lightweight **\*\*Hexagonal Architecture\*\***, also known as **\*\*Ports and Adapters\*\***.

The purpose of this design is not architectural complexity for its own sake. It keeps the core streaming and session-management logic independent from external technologies such as Gemini, WebSockets, FastAPI, FFmpeg, or the browser.

\`\`\`text

backend/

├── domain/

├── application/

├── ports/

├── adapters/

└── main.py

\`\`\`

**### Domain**

The domain contains the core business concepts of Josefina.

Examples:

\- \`ConferenceSession\`

\- \`CaptionSegment\`

These objects represent session and caption behavior without depending on FastAPI, Gemini, WebSockets, or infrastructure code.

**### Application**

The application layer coordinates the use cases and runtime behavior.

Examples:

\- \`SessionManager\`

\- \`StreamingOrchestrator\`

\- per-session runtimes

\- asynchronous audio queues

This layer coordinates how sessions are created, started, stopped, and processed.

**### Ports**

Ports define the contracts that the application expects from external services.

Examples:

\- \`SpeechEngine\`

\- \`CaptionPublisher\`

The application depends on these abstractions rather than directly on a specific provider.

For example, the streaming orchestrator depends on \`SpeechEngine\`, not on Gemini-specific implementation details.

**### Adapters**

Adapters connect the application to external technologies.

Current examples include:

\- \`GeminiAdapter\`

\- \`WebSocketCaptionPublisher\`

\- FastAPI HTTP endpoints

\- audio WebSocket input

This means a different speech provider could implement the same port without requiring changes to the core orchestration flow.

\`\`\`text

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

\`\`\`

\---

**## Real-time streaming flow**

The live path is:

\`\`\`text

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

\`\`\`

Audio is sent incrementally rather than waiting for a complete recording to finish.

That is the key design decision behind the low-latency experience.

\---

**## Multi-session model**

Each live conference session owns an independent runtime.

\`\`\`text

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

\`\`\`

This isolates live sessions at the application level and provides a clear path toward horizontal scaling.

The current hackathon MVP has not been load-tested at large scale, so no specific concurrency limit is claimed.

\---

**## Frontend**

The frontend separates production and audience responsibilities.

**### Production dashboard**

\`\`\`text

/producer

\`\`\`

The producer can:

\- create sessions;

\- see existing sessions;

\- see whether a producer is connected;

\- see viewer counts;

\- open producer interfaces;

\- open viewer interfaces;

\- close sessions.

**### Producer session**

\`\`\`text

/session/\<session_id>/producer

\`\`\`

The producer can:

\- start and stop microphone capture;

\- see live captions;

\- copy the viewer link;

\- close the session.

**### Viewer session**

\`\`\`text

/session/\<session_id>/viewer

\`\`\`

The audience receives translated captions without access to production controls.

\---


---

## Interfaces and roles

Josefina separates event operation from audience consumption through two main session interfaces: **Producer** and **Viewer**.

### Producer interface

Route:

```text
/session/<session_id>/producer
```

The producer interface is the live control surface for a specific talk or session.

From this screen, the producer can:

- start microphone capture;
- stop microphone capture explicitly;
- monitor whether the session is prepared or live;
- see translated captions while the speaker is talking;
- copy the public viewer link;
- return to the production dashboard without intentionally stopping the session;
- close the session when the talk finishes.

When the microphone starts, the browser captures audio with `MediaRecorder` and sends WebM/Opus chunks every 500 ms through the session audio WebSocket.

The producer interface keeps microphone control separate from session control:

```text
Start microphone
    ↓
audio capture begins
    ↓
session starts transmitting

Stop microphone
    ↓
audio capture stops
    ↓
session still exists

Close session
    ↓
audio capture stops
    ↓
backend session becomes CLOSED
```

This distinction is important during a real event: stopping the microphone does not necessarily mean closing the conference session.

### Viewer interface

Route:

```text
/session/<session_id>/viewer
```

The viewer interface is intentionally simpler.

A viewer can:

- open the shared session link;
- connect to the caption WebSocket;
- receive translated captions in real time;
- see the current caption/connection state;
- identify the session being watched.

The viewer cannot:

- start or stop the microphone;
- close the session;
- access production controls.

No account or installation is required. The audience only needs the shared browser URL.

The viewer receives caption messages with two caption states:

```text
live
closed
```

`live` means the current caption segment is still being built.

`closed` means the current caption segment has been completed.

The viewer interface presents these events as human-readable states such as:

```text
Connecting...
Connected
Live translation
Segment complete
Connection closed
Connection error
```

---

## Session lifecycle

A Josefina talk has a small and explicit lifecycle.

At the domain level, a conference session can move through:

```text
READY
  ↓
LIVE
  ↓
CLOSED
```

### READY

The session has been created and is available in the production dashboard, but no active audio producer is transmitting yet.

### LIVE

The session has an active producer/audio flow.

Typical flow:

```text
Producer starts microphone
        ↓
Browser captures WebM/Opus
        ↓
Audio WebSocket
        ↓
FFmpeg -> PCM
        ↓
Per-session audio queue
        ↓
Gemini Live
        ↓
Translated captions
        ↓
Viewer WebSocket
```

During this state, the production dashboard can show the producer as connected and viewers can receive captions continuously.

### CLOSED

The producer or production dashboard explicitly closes the session.

Closing a session:

- stops the active processing runtime;
- disconnects the producer audio path;
- prevents the session from being reopened as an active session;
- keeps the session visible as closed in the production dashboard.

The lifecycle is intentionally simple:

```text
CREATE SESSION
      ↓
    READY
      ↓
START MICROPHONE / PRODUCER CONNECTS
      ↓
     LIVE
      ↓
CLOSE SESSION
      ↓
    CLOSED
```

The MVP does not automatically close a talk simply because the producer navigates through the production interface. A session is closed only through an explicit close action.


**## Technology stack**

**### Backend**

\- Python

\- FastAPI

\- asyncio

\- WebSockets

\- FFmpeg

\- Gemini Live API

**### Frontend**

\- Next.js

\- React

\- TypeScript

\- MediaRecorder API

\- WebSockets

\- Tailwind CSS

**### Deployment**

\- Docker

\- Docker Compose

\---

**## Environment variables**

Create a \`.env\` file in the project root:

\`\`\`env

GEMINI_API_KEY=your_api_key_here

\`\`\`

**\*\*Never commit \`.env\` or API keys to the repository.\*\***

A recommended \`.gitignore\` includes:

\`\`\`gitignore

.env

.venv/

node_modules/

.next/

\_\_pycache\_\_/

\*.pyc

\`\`\`

\---

**## Quick start with Docker Compose**

The easiest way to run Josefina is with Docker Compose.

**### Requirements**

You only need:

\- Docker

\- Docker Compose

\- a Gemini API key

From the project root:

\`\`\`bash

docker compose up --build

\`\`\`

Docker Compose starts:

\- the FastAPI backend on port \`8000\`;

\- the Next.js frontend on port \`3000\`;

\- FFmpeg inside the backend container.

Then open:

\`\`\`text

http\://localhost:3000/producer

\`\`\`

Backend health check:

\`\`\`text

http\://localhost:8000/health

\`\`\`

A successful response looks like:

\`\`\`json

{

  "status": "ok",

  "service": "Josefina"

}

\`\`\`

To stop Josefina:

\`\`\`bash

docker compose down

\`\`\`

\---

**## Running without Docker**

Docker Compose is the recommended local deployment path, but the services can also be run manually.

**### Backend**

Create and activate a Python virtual environment:

\`\`\`bash

python3 -m venv .venv

source .venv/bin/activate

\`\`\`

Install dependencies:

\`\`\`bash

pip install -r requirements.txt

\`\`\`

Make sure FFmpeg is installed on the host:

\`\`\`bash

ffmpeg -version

\`\`\`

Start the API:

\`\`\`bash

uvicorn backend.main\:app --reload --host 0.0.0.0 --port 8000

\`\`\`

**### Frontend**

Open another terminal:

\`\`\`bash

cd frontend

npm install

npm run dev

\`\`\`

Then open:

\`\`\`text

http\://localhost:3000/producer

\`\`\`

\---

**## API overview**

The current MVP exposes session-management endpoints such as:

\`\`\`text

POST   /sessions

GET    /sessions

GET    /sessions/{session_id}

DELETE /sessions/{session_id}

\`\`\`

Real-time communication uses separate WebSockets for audio and captions:

\`\`\`text

/ws/audio/{session_id}

/ws/captions/{session_id}

\`\`\`

This keeps producer audio transport separate from viewer caption delivery.

\---

**## Quality**

Josefina processes continuous live speech instead of waiting for complete prerecorded files.

Translation quality depends on factors such as:

\- microphone quality;

\- background noise;

\- speaker pronunciation;

\- network conditions;

\- speech model performance;

\- technical vocabulary.

For the Vibeathon demo, the system is intended to be demonstrated with both normal speech and technical terminology.

\---

**## Latency**

The application is designed around streaming.

\`\`\`text

microphone

-> 500 ms WebM/Opus chunks

-> WebSocket

-> FFmpeg

-> PCM

-> Gemini Live

-> caption assembly

-> WebSocket

-> viewer

\`\`\`

The system does not wait for an entire talk or recording to finish before generating captions.

\---

**## Scalability**

The current MVP isolates sessions by design.

Each active session has its own:

\- runtime;

\- audio queue;

\- producer state;

\- speech connection;

\- viewer group.

Creating another conference session does not require changing the processing architecture.

A production evolution could distribute independent sessions across multiple backend workers or machines and move shared session state to infrastructure such as Redis.

\---

**## Deployment**

Josefina now includes a containerized deployment for both frontend and backend.

The project includes:

\`\`\`text

Josefina/

├── backend/

│   └── Dockerfile

├── frontend/

│   └── Dockerfile

├── docker-compose.yml

├── requirements.txt

└── .env

\`\`\`

The backend image installs FFmpeg and Python dependencies, while the frontend runs Next.js in its own container.

The complete MVP can be started with:

\`\`\`bash

docker compose up --build

\`\`\`

This reduces local setup and provides a reproducible way to run the same frontend/backend stack.

The current Compose deployment is intentionally simple: it contains the services needed for the hackathon MVP and avoids adding unnecessary infrastructure before it is required.

A future production topology could add a reverse proxy, distributed state, observability, and multiple backend instances:

\`\`\`text

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

\`\`\`

\---

**## Innovation**

Josefina is not only a speech-to-text demo.

The MVP models a real event-production workflow:

\- a producer creates and manages multiple live sessions;

\- every session has an independent speaker/audio path;

\- viewers receive a shareable link;

\- audience users do not need an account or installation;

\- production and audience interfaces are separated;

\- sessions can be centrally closed from the production console;

\- the full stack can be started using Docker Compose.

The focus is on making real-time multilingual captions operationally useful during an event.

\---

**## Current limitations**

This is a hackathon MVP.

Current limitations include:

\- English-to-Spanish is the primary configured translation path;

\- session state is stored in memory;

\- sessions are lost when the backend restarts;

\- there is no persistent database yet;

\- there is no authentication yet;

\- there is no distributed session registry yet;

\- the project has not been load-tested at production scale;

\- the current Docker Compose setup is intended for the MVP rather than a distributed production cluster.

These choices were intentional to prioritize the complete real-time user flow during the Vibeathon.

\---

**## What's next**

Possible next steps include:

\- additional source and target languages;

\- automatic language detection;

\- persistent session storage;

\- Redis-based distributed session state;

\- horizontal backend scaling;

\- production-ready Docker images and deployment profiles;

\- reverse proxy and TLS termination;

\- producer authentication;

\- event and room management;

\- downloadable transcripts;

\- caption history;

\- accessibility customization;

\- domain glossaries for technical events;

\- latency and quality metrics;

\- production observability.

\---

**## Built for Nerdearla Vibeathon 2026**

Josefina was created during the **\*\*Nerdearla Vibeathon 2026\*\***.

The project explores how streaming architecture, browser-native audio capture, modern speech models, and a lightweight production workflow can make multilingual live events more accessible.

\---

**## License**

This project is released under the **\*\*MIT License\*\***.

Copyright (c) 2026 Leonardo Martinelli

See the \`LICENSE\` file for details.