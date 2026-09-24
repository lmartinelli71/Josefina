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
PCM_SAMPLE_RATE = 16000
PCM_CHANNELS = 1
PCM_SAMPLE_WIDTH = 2

PCM_CHUNK_BYTES = int(
    PCM_SAMPLE_RATE
    * PCM_CHANNELS
    * PCM_SAMPLE_WIDTH
    * CHUNK_MS
    / 1000
)

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
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

    finally:
        caption_publisher.disconnect(
            session_id=session_id,
            websocket=websocket,
        )


# ---------------------------------
# WEBSOCKET DE AUDIO
# ---------------------------------

@app.websocket("/ws/audio/{session_id}")
async def audio_websocket(
    websocket: WebSocket,
    session_id: str,
):
    await websocket.accept()

    print(
        f"[{session_id}] "
        f"cliente de audio conectado",
        flush=True,
    )

    # ---------------------------------
    # PREPARAMOS LA SESIÓN
    # ---------------------------------

    if session_id not in session_manager.sessions:
        session_manager.create_session(
            session_id=session_id,
            name="Sesión en vivo Josefina",
            source_language="en",
            target_languages=["es"],
        )

    if session_id not in session_manager.runtimes:
        runtime = session_manager.start_session(
            session_id
        )
    else:
        runtime = session_manager.get_runtime(
            session_id
        )

    # Iniciamos el consumidor si todavía
    # no está corriendo.
    if (
        runtime.consumer_task is None
        or runtime.consumer_task.done()
    ):
        runtime.consumer_task = asyncio.create_task(
            orchestrator.consume_audio(
                session_id
            )
        )

    # ---------------------------------
    # FFMPEG
    # WebM/Opus -> PCM s16le 16 kHz mono
    # ---------------------------------

    ffmpeg = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-loglevel",
        "error",

        # entrada desde stdin
        "-i",
        "pipe:0",

        # sin video
        "-vn",

        # mono
        "-ac",
        str(PCM_CHANNELS),

        # 16 kHz
        "-ar",
        str(PCM_SAMPLE_RATE),

        # PCM signed 16-bit little endian
        "-f",
        "s16le",

        # salida a stdout
        "pipe:1",

        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # ---------------------------------
    # TAREA:
    # FFMPEG -> AUDIO QUEUE
    # ---------------------------------

    async def read_pcm():
        try:
            while True:
                pcm_chunk = await ffmpeg.stdout.read(
                    PCM_CHUNK_BYTES
                )

                if not pcm_chunk:
                    break

                await runtime.audio_queue.put(
                    pcm_chunk
                )

                print(
                    f"[{session_id}] "
                    f"PCM -> queue: "
                    f"{len(pcm_chunk)} bytes",
                    flush=True,
                )

        except asyncio.CancelledError:
            pass

    pcm_task = asyncio.create_task(
        read_pcm()
    )

    # ---------------------------------
    # NAVEGADOR -> FFMPEG
    # ---------------------------------

    try:
        while True:
            data = await websocket.receive_bytes()

            print(
                f"[{session_id}] "
                f"WebM recibido: "
                f"{len(data)} bytes",
                flush=True,
            )

            if ffmpeg.stdin is not None:
                ffmpeg.stdin.write(data)

                await ffmpeg.stdin.drain()

    except WebSocketDisconnect:

        print(
            f"[{session_id}] "
            f"cliente de audio desconectado",
            flush=True,
        )

    finally:

        # Cerramos la entrada de ffmpeg.
        if ffmpeg.stdin is not None:
            try:
                ffmpeg.stdin.close()
            except Exception:
                pass

        # Esperamos que termine de procesar
        # lo que quede en el buffer.
        try:
            await asyncio.wait_for(
                ffmpeg.wait(),
                timeout=2.0,
            )
        except asyncio.TimeoutError:
            ffmpeg.kill()
            await ffmpeg.wait()

        if not pcm_task.done():
            pcm_task.cancel()

        try:
            await pcm_task
        except asyncio.CancelledError:
            pass