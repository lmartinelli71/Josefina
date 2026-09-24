import os
import asyncio

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from backend.ports.speech_engine import SpeechEngine
from backend.domain.conference_session import ConferenceSession


class GeminiAdapter(SpeechEngine):
    """
    Implementación de SpeechEngine utilizando Gemini.

    Gestiona:
    - traducción de texto;
    - transcripción batch de archivos;
    - transcripción Live de audio PCM;
    - traducción Live en tiempo real.
    """

    def __init__(self):
        load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY no está definida en el archivo .env"
            )

        self.client = genai.Client(api_key=api_key)

    async def translate_text(
        self,
        text: str,
        target_language: str,
    ) -> str:
        """
        Traduce un texto al idioma solicitado.

        Se mantiene como fallback y para pruebas.
        """

        prompt = f"""
Translate the following text into natural {target_language}.

Return only the translation, without explanations.

TEXT:

{text}
"""

        response = await self._generate_with_retry(
            model="gemini-3.5-flash-lite",
            contents=prompt,
        )

        if not response.text:
            raise RuntimeError(
                "Gemini respondió, pero no devolvió texto traducido."
            )

        return response.text.strip()

    async def transcribe_file(
        self,
        file_path: str,
    ) -> str:
        """
        Transcribe un archivo completo de audio.

        Se mantiene para pruebas batch y como posible fallback.
        """

        audio_file = await asyncio.to_thread(
            self.client.files.upload,
            file=file_path,
        )

        response = await self._generate_with_retry(
            model="gemini-3.5-transcribe",
            contents=[audio_file],
        )

        transcripts = []

        for candidate in response.candidates or []:
            content = candidate.content

            if content is None:
                continue

            for part in content.parts or []:
                audio_transcription = getattr(
                    part,
                    "audio_transcription",
                    None,
                )

                if audio_transcription is None:
                    continue

                text = getattr(
                    audio_transcription,
                    "text",
                    None,
                )

                if text:
                    transcripts.append(text)

        if not transcripts:
            raise RuntimeError(
                "Gemini respondió al audio, pero no se pudo "
                "extraer ninguna transcripción."
            )

        return " ".join(transcripts).strip()

    def live_connection(self):
        """
        Conexión Live dedicada solamente a transcripción.

        Se mantiene como fallback y para pruebas.
        """

        config = types.LiveConnectConfig(
            response_modalities=["TEXT"],
            input_audio_transcription=types.AudioTranscriptionConfig(
                language_codes=[]
            ),
        )

        return self.client.aio.live.connect(
            model="gemini-3.5-transcribe-live",
            config=config,
        )

    def live_translate_connection(
        self,
        target_language: str = "es",
    ):
        """
        Abre una conexión persistente con Gemini Live Translate.

        Recibe audio continuo y genera:
        - transcripción del idioma original;
        - traducción incremental al idioma destino.
        """

        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],

            input_audio_transcription=
                types.AudioTranscriptionConfig(),

            output_audio_transcription=
                types.AudioTranscriptionConfig(),

            translation_config=
                types.TranslationConfig(
                    target_language_code=target_language,
                    echo_target_language=True,
                ),
        )

        return self.client.aio.live.connect(
            model="gemini-3.5-live-translate-preview",
            config=config,
        )

    async def send_live_audio(
        self,
        live_session,
        chunk: bytes,
        sample_rate: int = 16000,
    ) -> None:
        """
        Envía un chunk PCM crudo a una sesión Live activa.

        El audio esperado es PCM 16-bit, mono y little-endian.
        """

        await live_session.send_realtime_input(
            audio=types.Blob(
                data=chunk,
                mime_type=f"audio/pcm;rate={sample_rate}",
            )
        )

    async def end_live_audio(
        self,
        live_session,
    ) -> None:
        """
        Indica a Gemini que terminó el flujo actual de audio.
        """

        await live_session.send_realtime_input(
            audio_stream_end=True
        )

    async def receive_live_transcriptions(
        self,
        live_session,
    ):
        """
        Produce transcripciones parciales y finales
        desde Gemini Live Transcribe.

        Devuelve:
        {
            "type": "interim" | "final",
            "text": "..."
        }
        """

        async for message in live_session.receive():

            server_content = getattr(
                message,
                "server_content",
                None,
            )

            if server_content is None:
                continue

            interim = getattr(
                server_content,
                "interim_input_transcription",
                None,
            )

            if interim is not None:
                text = getattr(
                    interim,
                    "text",
                    None,
                )

                if text:
                    yield {
                        "type": "interim",
                        "text": text.strip(),
                    }

            final = getattr(
                server_content,
                "input_transcription",
                None,
            )

            if final is not None:
                text = getattr(
                    final,
                    "text",
                    None,
                )

                if text:
                    yield {
                        "type": "final",
                        "text": text.strip(),
                    }

    async def receive_live_translation(
        self,
        live_session,
    ):
        """
        Produce eventos normalizados de Gemini Live Translate.

        Devuelve:
        {
            "type": "source",
            "text": "..."
        }

        o:

        {
            "type": "translation",
            "text": "..."
        }
        """

        async for message in live_session.receive():

            server_content = getattr(
                message,
                "server_content",
                None,
            )

            if server_content is None:
                continue

            source = getattr(
                server_content,
                "input_transcription",
                None,
            )

            if source is not None:
                text = getattr(
                    source,
                    "text",
                    None,
                )

                if text:
                    yield {
                        "type": "source",
                        "text": text.strip(),
                    }

            translation = getattr(
                server_content,
                "output_transcription",
                None,
            )

            if translation is not None:
                text = getattr(
                    translation,
                    "text",
                    None,
                )

                if text:
                    yield {
                        "type": "translation",
                        "text": text.strip(),
                    }

    async def _generate_with_retry(
        self,
        model: str,
        contents,
        max_attempts: int = 3,
    ):
        """
        Ejecuta una llamada normal a Gemini y reintenta
        automáticamente ante errores temporales 503.
        """

        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                return await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=model,
                    contents=contents,
                )

            except errors.ServerError as exc:
                last_error = exc

                if exc.code != 503 or attempt == max_attempts:
                    raise

                wait_seconds = 2 ** (attempt - 1)

                print(
                    f"Gemini temporalmente no disponible. "
                    f"Reintento {attempt}/{max_attempts} "
                    f"en {wait_seconds}s..."
                )

                await asyncio.sleep(wait_seconds)

        raise last_error

    async def send_audio(
        self,
        session: ConferenceSession,
        chunk: bytes,
    ) -> None:
        """
        Método requerido por SpeechEngine.

        Más adelante conectaremos este método con
        SessionRuntime y la conexión Live de cada sesión.
        """

        pass