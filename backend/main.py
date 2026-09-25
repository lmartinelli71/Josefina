import asyncio
import wave
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.application.session_manager import SessionManager
from backend.application.streaming_orchestrator import StreamingOrchestrator
from backend.adapters.outbound.gemini_adapter import GeminiAdapter
from backend.adapters.outbound.websocket_caption_publisher import (
    WebSocketCaptionPublisher,
)
from backend.domain.conference_session import SessionStatus


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
# CORS
# ---------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
# SERIALIZAR SESIÓN
# ---------------------------------

def session_to_dict(session):
    return {
        "session_id": session.id,
        "name": session.name,
        "status": session.status.value,
        "producer_connected": session.producer_connected,
        "viewer_count": session.viewer_count,
        "producer_url": (
            f"/session/{session.id}/producer"
        ),
        "viewer_url": (
            f"/session/{session.id}/viewer"
        ),
    }


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
# CREAR SESIÓN
# ---------------------------------

@app.post("/sessions")
async def create_session():
    """
    Crea una nueva ConferenceSession.
    """

    session_id = uuid4().hex[:8]

    session = session_manager.create_session(
        session_id=session_id,
        name="Sesión Josefina",
        source_language="en",
        target_languages=["es"],
    )

    return session_to_dict(
        session
    )


# ---------------------------------
# LISTAR SESIONES
# ---------------------------------

@app.get("/sessions")
async def list_sessions():
    """
    Devuelve todas las sesiones conocidas
    por el backend.
    """

    return [
        session_to_dict(session)
        for session
        in session_manager.list_sessions()
    ]


# ---------------------------------
# CONSULTAR UNA SESIÓN
# ---------------------------------

@app.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
):
    """
    Devuelve el estado actual de una sesión.
    """

    if session_id not in session_manager.sessions:
        return {
            "status": "not_found",
            "session_id": session_id,
        }

    session = session_manager.get_session(
        session_id
    )

    return session_to_dict(
        session
    )


# ---------------------------------
# CERRAR SESIÓN
# ---------------------------------

@app.delete("/sessions/{session_id}")
async def close_session(
    session_id: str,
):
    """
    Cierra definitivamente una sesión.

    CLOSED significa que ya no puede
    volver a transmitir.
    """

    if session_id not in session_manager.sessions:
        return {
            "status": "not_found",
            "session_id": session_id,
        }

    session = session_manager.get_session(
        session_id
    )

    # Primero marcamos la sesión CLOSED.
    # Así las conexiones activas pueden
    # detectar inmediatamente el cierre.
    session.close()

    # ---------------------------------
    # DETENER RUNTIME
    # ---------------------------------

    if session_id in session_manager.runtimes:

        runtime = session_manager.get_runtime(
            session_id
        )

        if (
            runtime.consumer_task is not None
            and not runtime.consumer_task.done()
        ):
            runtime.consumer_task.cancel()

            try:
                await runtime.consumer_task

            except asyncio.CancelledError:
                pass

        runtime.consumer_task = None

        session_manager.runtimes.pop(
            session_id,
            None,
        )

    return {
        "status": "closed",
        "session_id": session_id,
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

    while runtime.speech_connection is None:
        await asyncio.sleep(0.05)

    print(
        f"\n[{session_id}] "
        f"Gemini Live conectado. "
        f"Comenzando audio demo...\n",
        flush=True,
    )

    with wave.open(
        wav_path,
        "rb",
    ) as wav_file:

        sample_rate = (
            wav_file.getframerate()
        )

        frames_per_chunk = int(
            sample_rate
            * CHUNK_MS
            / 1000
        )

        while True:

            session = session_manager.get_session(
                session_id
            )

            if session.status == SessionStatus.CLOSED:
                break

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

    if session_id not in session_manager.sessions:

        session_manager.create_session(
            session_id=session_id,
            name="Demo Josefina",
            source_language="en",
            target_languages=["es"],
        )

    session = session_manager.get_session(
        session_id
    )

    if session.status == SessionStatus.CLOSED:
        return {
            "status": "closed",
            "session_id": session_id,
        }

    if session_id not in session_manager.runtimes:

        runtime = session_manager.start_session(
            session_id
        )

    else:

        runtime = session_manager.get_runtime(
            session_id
        )

    if (
        runtime.consumer_task is None
        or runtime.consumer_task.done()
    ):

        runtime.consumer_task = asyncio.create_task(
            orchestrator.consume_audio(
                session_id
            )
        )

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

@app.websocket(
    "/ws/captions/{session_id}"
)
async def caption_websocket(
    websocket: WebSocket,
    session_id: str,
):

    # Para el MVP todavía permitimos
    # crear automáticamente una sesión
    # si el ID no existe.
    if session_id not in session_manager.sessions:

        session_manager.create_session(
            session_id=session_id,
            name="Sesión Josefina",
            source_language="en",
            target_languages=["es"],
        )

    session = session_manager.get_session(
        session_id
    )

    # Una sesión cerrada ya no acepta
    # nuevas conexiones de subtítulos.
    if session.status == SessionStatus.CLOSED:
        await websocket.close(
            code=1008
        )
        return

    await caption_publisher.connect(
        session_id=session_id,
        websocket=websocket,
    )

    session_manager.add_viewer(
        session_id
    )

    print(
        f"[{session_id}] "
        f"viewer conectado. "
        f"Total viewers: "
        f"{session_manager.get_session(session_id).viewer_count}",
        flush=True,
    )

    try:

        while True:

            message = await websocket.receive()

            if (
                message["type"]
                == "websocket.disconnect"
            ):
                break

            session = session_manager.get_session(
                session_id
            )

            if session.status == SessionStatus.CLOSED:
                await websocket.close()
                break

    finally:

        session_manager.remove_viewer(
            session_id
        )

        caption_publisher.disconnect(
            session_id=session_id,
            websocket=websocket,
        )

        print(
            f"[{session_id}] "
            f"viewer desconectado. "
            f"Total viewers: "
            f"{session_manager.get_session(session_id).viewer_count}",
            flush=True,
        )


# ---------------------------------
# WEBSOCKET DE AUDIO
# ---------------------------------

@app.websocket(
    "/ws/audio/{session_id}"
)
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

    session = session_manager.get_session(
        session_id
    )


    # ---------------------------------
    # NO REABRIR SESIÓN CERRADA
    # ---------------------------------

    if session.status == SessionStatus.CLOSED:

        print(
            f"[{session_id}] "
            f"intento de conectar audio "
            f"a una sesión CLOSED",
            flush=True,
        )

        await websocket.close(
            code=1008
        )

        return


    # ---------------------------------
    # RUNTIME
    # ---------------------------------

    if session_id not in session_manager.runtimes:

        runtime = session_manager.start_session(
            session_id
        )

    else:

        runtime = session_manager.get_runtime(
            session_id
        )


    # ---------------------------------
    # PRODUCTOR
    # ---------------------------------

    try:
        session_manager.connect_producer(
            session_id
        )

    except ValueError:

        print(
            f"[{session_id}] "
            f"ya existe un productor conectado",
            flush=True,
        )

        await websocket.close(
            code=1008
        )

        return


    print(
        f"[{session_id}] "
        f"productor conectado",
        flush=True,
    )


    # ---------------------------------
    # INICIAMOS EL ORQUESTADOR
    # ---------------------------------

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

        "-i",
        "pipe:0",

        "-vn",

        "-ac",
        str(PCM_CHANNELS),

        "-ar",
        str(PCM_SAMPLE_RATE),

        "-f",
        "s16le",

        "pipe:1",

        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


    # ---------------------------------
    # FFMPEG -> AUDIO QUEUE
    # ---------------------------------

    async def read_pcm():

        try:

            while True:

                # Si la sesión fue cerrada
                # desde el panel, dejamos
                # de producir audio.
                session = (
                    session_manager.get_session(
                        session_id
                    )
                )

                if (
                    session.status
                    == SessionStatus.CLOSED
                ):
                    break

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

            # ---------------------------------
            # ¿LA SESIÓN FUE CERRADA?
            # ---------------------------------

            session = session_manager.get_session(
                session_id
            )

            if session.status == SessionStatus.CLOSED:

                print(
                    f"[{session_id}] "
                    f"sesión cerrada desde "
                    f"el panel de producción",
                    flush=True,
                )

                await websocket.close()

                break


            print(
                f"[{session_id}] "
                f"WebM recibido: "
                f"{len(data)} bytes",
                flush=True,
            )


            if ffmpeg.stdin is not None:

                ffmpeg.stdin.write(
                    data
                )

                await ffmpeg.stdin.drain()


    except WebSocketDisconnect:

        print(
            f"[{session_id}] "
            f"cliente de audio desconectado",
            flush=True,
        )


    finally:

        # ---------------------------------
        # PRODUCTOR DESCONECTADO
        # ---------------------------------

        session_manager.disconnect_producer(
            session_id
        )

        print(
            f"[{session_id}] "
            f"productor desconectado",
            flush=True,
        )


        # ---------------------------------
        # CERRAMOS FFMPEG
        # ---------------------------------

        if ffmpeg.stdin is not None:

            try:
                ffmpeg.stdin.close()

            except Exception:
                pass


        try:

            await asyncio.wait_for(
                ffmpeg.wait(),
                timeout=2.0,
            )

        except asyncio.TimeoutError:

            ffmpeg.kill()

            await ffmpeg.wait()


        # ---------------------------------
        # DETENEMOS TAREA PCM
        # ---------------------------------

        if not pcm_task.done():

            pcm_task.cancel()


        try:

            await pcm_task

        except asyncio.CancelledError:
            pass


        # ---------------------------------
        # DETENEMOS EL ORQUESTADOR
        # ---------------------------------

        if (
            runtime.consumer_task is not None
            and not runtime.consumer_task.done()
        ):

            runtime.consumer_task.cancel()

            try:

                await runtime.consumer_task

            except asyncio.CancelledError:
                pass


        runtime.consumer_task = None


        # Si la sesión sigue abierta,
        # mantenemos el runtime disponible
        # para una eventual reconexión.
        #
        # Si está CLOSED, eliminamos
        # definitivamente su runtime.
        session = session_manager.get_session(
            session_id
        )

        if session.status == SessionStatus.CLOSED:

            session_manager.runtimes.pop(
                session_id,
                None,
            )


        print(
            f"[{session_id}] "
            f"procesamiento de audio detenido",
            flush=True,
        )