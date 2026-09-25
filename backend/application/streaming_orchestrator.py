import asyncio

from backend.application.session_manager import SessionManager
from backend.application.caption_assembler import CaptionAssembler
from backend.ports.caption_publisher import CaptionPublisher
from backend.ports.speech_engine import SpeechEngine

class StreamingOrchestrator:
    """
    Coordina el flujo continuo de audio.

    audio_queue
        ↓
    Gemini Live Translate
        ↓
    original + traducción
        ↓
    CaptionAssembler
        ↓
    CaptionSegment LIVE / CLOSED
        ↓
    CaptionPublisher
        ↓
    navegador
    """

    def __init__(
        self,
        session_manager: SessionManager,
        speech_engine: SpeechEngine,
        caption_publisher: CaptionPublisher | None = None,
    ):
        self.session_manager = session_manager
        self.speech_engine = speech_engine
        self.caption_publisher = caption_publisher

    async def consume_audio(
        self,
        session_id: str,
    ):
        session = self.session_manager.get_session(
            session_id
        )

        runtime = self.session_manager.get_runtime(
            session_id
        )

        if not session.target_languages:
            raise RuntimeError(
                "La sesión no tiene idioma destino."
            )

        target_language = (
            session.target_languages[0]
        )

        assembler = CaptionAssembler(
            session_id=session_id,
            language=target_language,
        )

        async with (
            self.speech_engine
            .live_translate_connection(
                target_language=target_language
            )
        ) as live_session:

            runtime.speech_connection = live_session

            receiver_task = asyncio.create_task(
                self.receive_translations(
                    session_id=session_id,
                    live_session=live_session,
                    assembler=assembler,
                    target_language=target_language,
                )
            )

            try:
                while True:
                    chunk = await runtime.audio_queue.get()

                    try:
                        await (
                            self.speech_engine
                            .send_live_audio(
                                live_session=live_session,
                                chunk=chunk,
                            )
                        )

                    finally:
                        runtime.audio_queue.task_done()

            except asyncio.CancelledError:
                await (
                    self.speech_engine
                    .end_live_audio(
                        live_session=live_session
                    )
                )

                raise

            finally:
                receiver_task.cancel()

                try:
                    await receiver_task

                except asyncio.CancelledError:
                    pass

                runtime.speech_connection = None

    async def receive_translations(
        self,
        session_id: str,
        live_session,
        assembler: CaptionAssembler,
        target_language: str,
    ):
        """
        Recibe continuamente los eventos de Gemini.

        El original se conserva como diagnóstico.

        La traducción:
        - alimenta CaptionAssembler;
        - produce CaptionSegment;
        - publica segmentos LIVE y CLOSED.
        """

        async for event in (
            self.speech_engine
            .receive_live_translation(
                live_session
            )
        ):

            if event["type"] == "source":
                print(
                    f"\n[{session_id}] "
                    f"ORIGINAL:\n"
                    f"{event['text']}",
                    flush=True,
                )

            elif event["type"] == "translation":

                result = assembler.add_translation(
                    event["text"]
                )

                # ---------------------------------
                # SEGMENTOS CERRADOS
                # ---------------------------------

                for segment in (
                    result["closed_segments"]
                ):

                    text = segment.texts.get(
                        target_language,
                        "",
                    )

                    print(
                        f"\n[{session_id}] "
                        f"SUBTÍTULO [CERRADO]:\n"
                        f"{text}",
                        flush=True,
                    )

                    self._publish_without_blocking(
                        session_id=session_id,
                        payload={
                            "type": "caption",
                            "status": segment.status.value.lower(),
                            "text": text,
                            "start_time": segment.start_time,
                            "end_time": segment.end_time,
                        },
                    )

                # ---------------------------------
                # SUBTÍTULO LIVE
                # ---------------------------------

                current_segment = result["current"]

                if current_segment is not None:

                    text = current_segment.texts.get(
                        target_language,
                        "",
                    )

                    if text:
                        print(
                            f"\n[{session_id}] "
                            f"SUBTÍTULO [LIVE]:\n"
                            f"{text}",
                            flush=True,
                        )

                        self._publish_without_blocking(
                            session_id=session_id,
                            payload={
                                "type": "caption",
                                "status": current_segment.status.value.lower(),
                                "text": text,
                                "start_time": current_segment.start_time,
                                "end_time": current_segment.end_time,
                            },
                        )

    def _publish_without_blocking(
        self,
        session_id: str,
        payload: dict,
    ) -> None:
        """
        Publica el subtítulo sin bloquear
        el procesamiento de Gemini.

        Si no hay publisher configurado,
        simplemente no hace nada.
        """

        if self.caption_publisher is None:
            return

        asyncio.create_task(
            self._safe_publish(
                session_id=session_id,
                payload=payload,
            )
        )

    async def _safe_publish(
        self,
        session_id: str,
        payload: dict,
    ) -> None:
        """
        Evita que un error de WebSocket
        afecte al pipeline de traducción.
        """

        try:
            await self.caption_publisher.publish(
                session_id=session_id,
                payload=payload,
            )

        except Exception as exc:
            print(
                f"\n[{session_id}] "
                f"Error publicando subtítulo: "
                f"{exc}",
                flush=True,
            )