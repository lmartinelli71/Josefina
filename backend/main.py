import asyncio
import wave

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.application.session_manager import SessionManager
from backend.application.streaming_orchestrator import StreamingOrchestrator
from backend.adapters.outbound.gemini_adapter import GeminiAdapter
from backend.adapters.outbound.websocket_caption_publisher import (
    WebSocketCaptionPublisher,
)


CHUNK_MS = 100


app = FastAPI(
    title="Josefina",
    version="0.1.0",
)


# ---------------------------------
# COMPONENTES COMPARTIDOS
# ---------------------------------

session_manager = SessionManager()

speech_engine = GeminiAdapter()

caption_publisher = WebSocketCaptionPublisher()

orchestrator = StreamingOrchestrator(
    session_manager=session_manager,
    speech_engine=speech_engine,
    caption_publisher=caption_publisher,
)


# ---------------------------------
# HEALTH
# ---------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "Josefina",
    }


# ---------------------------------
# ENDPOINT TEMPORAL DE PRUEBA
# ---------------------------------

@app.get("/test-caption/{session_id}")
async def test_caption(
    session_id: str,
):
    await caption_publisher.publish(
        session_id=session_id,
        payload={
            "type": "caption",
            "status": "live",
            "text": "Hola desde Josefina",
        },
    )

    return {
        "status": "sent",
        "session_id": session_id,
    }


# ---------------------------------
# AUDIO DEMO
# ---------------------------------

async def feed_demo_audio(
    session_id: str,
    wav_path: str = "english.wav",
):
    runtime = session_manager.get_runtime(
        session_id
    )

    # Esperamos a que Gemini Live
    # esté realmente conectado.
    while runtime.speech_connection is None:
        await asyncio.sleep(0.05)

    print(
        f"\n[{session_id}] "
        f"Gemini Live conectado. "
        f"Comenzando audio demo...\n",
        flush=True,
    )

    with wave.open(wav_path, "rb") as wav_file:
        sample_rate = wav_file.getframerate()

        frames_per_chunk = int(
            sample_rate * CHUNK_MS / 1000
        )

        while True:
            chunk = wav_file.readframes(
                frames_per_chunk
            )

            if not chunk:
                break

            await runtime.audio_queue.put(
                chunk
            )

            await asyncio.sleep(
                CHUNK_MS / 1000
            )

    print(
        f"\n[{session_id}] "
        f"Audio demo terminado.",
        flush=True,
    )


# ---------------------------------
# INICIAR DEMO
# ---------------------------------

@app.get("/demo/start/{session_id}")
async def start_demo(
    session_id: str,
):
    # Creamos la sesión si todavía no existe.
    if session_id not in session_manager.sessions:

        session_manager.create_session(
            session_id=session_id,
            name="Demo Josefina",
            source_language="en",
            target_languages=["es"],
        )

    # Creamos el runtime si todavía no existe.
    if session_id not in session_manager.runtimes:

        runtime = session_manager.start_session(
            session_id
        )

    else:

        runtime = session_manager.get_runtime(
            session_id
        )

    # Iniciamos el orquestador solamente
    # si todavía no hay uno corriendo.
    if (
        runtime.consumer_task is None
        or runtime.consumer_task.done()
    ):

        runtime.consumer_task = asyncio.create_task(
            orchestrator.consume_audio(
                session_id
            )
        )

    # El audio corre como tarea separada
    # para que el endpoint responda inmediatamente.
    asyncio.create_task(
        feed_demo_audio(
            session_id=session_id,
            wav_path="english.wav",
        )
    )

    return {
        "status": "started",
        "session_id": session_id,
    }


# ---------------------------------
# WEBSOCKET DE SUBTÍTULOS
# ---------------------------------

@app.websocket("/ws/captions/{session_id}")
async def caption_websocket(
    websocket: WebSocket,
    session_id: str,
):
    await caption_publisher.connect(
        session_id=session_id,
        websocket=websocket,
    )

    try:

        while True:
            await websocket.receive()

    except WebSocketDisconnect:

        caption_publisher.disconnect(
            session_id=session_id,
            websocket=websocket,
        )