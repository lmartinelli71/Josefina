import asyncio
import wave

from backend.application.session_manager import SessionManager
from backend.application.streaming_orchestrator import StreamingOrchestrator
from backend.adapters.outbound.gemini_adapter import GeminiAdapter


CHUNK_MS = 100


async def feed_audio(
    manager: SessionManager,
    session_id: str,
    wav_path: str,
):
    runtime = manager.get_runtime(session_id)

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

            await runtime.audio_queue.put(chunk)

            if runtime.audio_queue.qsize() > 1:
                print(
                    f"[QUEUE] backlog: "
                    f"{runtime.audio_queue.qsize()} chunks",
                    flush=True,
                )

            await asyncio.sleep(
                CHUNK_MS / 1000
            )

    print("\nAudio terminado.", flush=True)


async def main():
    manager = SessionManager()
    adapter = GeminiAdapter()

    orchestrator = StreamingOrchestrator(
        session_manager=manager,
        speech_engine=adapter,
    )

    session_id = "demo-001"

    manager.create_session(
        session_id=session_id,
        name="Prueba Josefina",
        source_language="en",
        target_languages=["es"],
    )

    manager.start_session(
        session_id
    )

    print("Sesión creada.")
    print("Iniciando orquestador...\n")

    orchestrator_task = asyncio.create_task(
        orchestrator.consume_audio(
            session_id
        )
    )

    # Esperamos a que Gemini Live esté conectado
    # antes de comenzar a enviar audio.
    runtime = manager.get_runtime(
        session_id
    )

    while runtime.speech_connection is None:
        await asyncio.sleep(0.05)

    print(
        "Gemini Live conectado. "
        "Comenzando audio...\n",
        flush=True,
    )

    await feed_audio(
        manager=manager,
        session_id=session_id,
        wav_path="english.wav",
    )

    await runtime.audio_queue.join()

    # Por ahora mantenemos esta espera
    # para observar cuánto queda pendiente.
    await asyncio.sleep(15)

    orchestrator_task.cancel()

    try:
        await orchestrator_task

    except asyncio.CancelledError:
        pass

    manager.stop_session(
        session_id
    )

    print("\nSesión finalizada.")


if __name__ == "__main__":
    asyncio.run(main())