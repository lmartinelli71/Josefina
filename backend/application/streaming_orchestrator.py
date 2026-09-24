import asyncio

from backend.application.session_manager import SessionManager
from backend.application.caption_assembler import CaptionAssembler


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
    subtítulo traducido en vivo
    """

    def __init__(
        self,
        session_manager: SessionManager,
        speech_engine,
    ):
        self.session_manager = session_manager
        self.speech_engine = speech_engine

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

        assembler = CaptionAssembler()

        async with (
            self.speech_engine
            .live_translate_connection(
                target_language=target_language
            )
        ) as live_session:

            runtime.speech_connection = (
                live_session
            )

            receiver_task = (
                asyncio.create_task(
                    self.receive_translations(
                        session_id=session_id,
                        live_session=live_session,
                        assembler=assembler,
                    )
                )
            )

            try:

                while True:

                    chunk = (
                        await runtime
                        .audio_queue
                        .get()
                    )

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
    ):
        """
        Recibe continuamente los eventos de Gemini.

        El original se conserva como diagnóstico.
        La traducción es la que controla
        los subtítulos visibles.
        """

        async for event in (
            self.speech_engine
            .receive_live_translation(
                live_session
            )
        ):

            if event["type"] == "source":

                # Solo diagnóstico.
                print(
                    f"\n[{session_id}] "
                    f"ORIGINAL:\n"
                    f"{event['text']}",
                    flush=True,
                )

            elif event["type"] == "translation":

                result = (
                    assembler.add_translation(
                        event["text"]
                    )
                )

                # Segmentos que acaban de terminar.
                for closed_text in (
                    result["closed_segments"]
                ):

                    print(
                        f"\n[{session_id}] "
                        f"SUBTÍTULO [CERRADO]:\n"
                        f"{closed_text}",
                        flush=True,
                    )

                # Este es el texto que irá
                # cambiando en pantalla mientras habla.
                if result["current"]:

                    print(
                        f"\n[{session_id}] "
                        f"SUBTÍTULO [LIVE]:\n"
                        f"{result['current']}",
                        flush=True,
                    )