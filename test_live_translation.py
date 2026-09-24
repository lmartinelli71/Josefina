import asyncio
import time
import wave

from google.genai import types

from backend.adapters.outbound.gemini_adapter import GeminiAdapter


CHUNK_MS = 100


async def sender(
    session,
    wav_path: str,
):
    """
    Envía un WAV PCM a Gemini Live Translate
    respetando aproximadamente el tiempo real.
    """

    with wave.open(wav_path, "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()

        print(f"Canales: {channels}")
        print(f"Sample width: {sample_width * 8} bits")
        print(f"Sample rate: {sample_rate} Hz")

        if channels != 1:
            raise RuntimeError(
                "El WAV debe ser mono."
            )

        if sample_width != 2:
            raise RuntimeError(
                "El WAV debe ser PCM de 16 bits."
            )

        frames_per_chunk = int(
            sample_rate * CHUNK_MS / 1000
        )

        while True:
            chunk = wav_file.readframes(
                frames_per_chunk
            )

            if not chunk:
                break

            await session.send_realtime_input(
                audio=types.Blob(
                    data=chunk,
                    mime_type=(
                        f"audio/pcm;rate={sample_rate}"
                    ),
                )
            )

            await asyncio.sleep(
                CHUNK_MS / 1000
            )

        await session.send_realtime_input(
            audio_stream_end=True
        )


async def receiver(
    session,
    start_time: float,
):
    """
    Muestra transcripción original y traducción
    a medida que Gemini las produce.
    """

    async for response in session.receive():

        elapsed = (
            time.monotonic()
            - start_time
        )

        server_content = getattr(
            response,
            "server_content",
            None,
        )

        if server_content is None:
            continue

        input_transcription = getattr(
            server_content,
            "input_transcription",
            None,
        )

        if (
            input_transcription is not None
            and input_transcription.text
        ):
            print(
                f"[{elapsed:6.2f}s] EN: "
                f"{input_transcription.text}",
                flush=True,
            )

        output_transcription = getattr(
            server_content,
            "output_transcription",
            None,
        )

        if (
            output_transcription is not None
            and output_transcription.text
        ):
            print(
                f"[{elapsed:6.2f}s] ES: "
                f"{output_transcription.text}",
                flush=True,
            )


async def main():

    adapter = GeminiAdapter()

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],

        input_audio_transcription=
            types.AudioTranscriptionConfig(),

        output_audio_transcription=
            types.AudioTranscriptionConfig(),

        translation_config=
            types.TranslationConfig(
                target_language_code="es",
                echo_target_language=True,
            ),
    )

    print(
        "Abriendo Gemini Live Translate..."
    )

    async with adapter.client.aio.live.connect(
        model="gemini-3.5-live-translate-preview",
        config=config,
    ) as session:

        print(
            "Conexión establecida.\n"
        )

        start_time = time.monotonic()

        send_task = asyncio.create_task(
            sender(
                session,
                "english.wav",
            )
        )

        receive_task = asyncio.create_task(
            receiver(
                session,
                start_time,
            )
        )

        await send_task

        try:
            await asyncio.wait_for(
                receive_task,
                timeout=5,
            )

        except asyncio.TimeoutError:
            receive_task.cancel()

            try:
                await receive_task

            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    asyncio.run(main())