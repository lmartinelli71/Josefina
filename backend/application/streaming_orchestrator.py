import asyncio

from backend.application.session_manager import SessionManager


class StreamingOrchestrator:
    """
    Coordina el flujo continuo de audio de una sesión activa.

    Flujo:

        audio_queue
            ↓
        Gemini Live Translate
            ↓
        transcripción original
            ↓
        traducción
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
        """
        Mantiene una conexión persistente con Gemini Live Translate
        y consume continuamente los chunks de audio de la cola FIFO.
        """

        session = self.session_manager.get_session(
            session_id
        )

        runtime = self.session_manager.get_runtime(
            session_id
        )

        if not session.target_languages:
            raise RuntimeError(
                "La sesión no tiene un idioma destino configurado."
            )

        # Para el MVP usamos un idioma destino.
        target_language = session.target_languages[0]

        async with self.speech_engine.live_translate_connection(
            target_language=target_language
        ) as live_session:

            # Guardamos la conexión activa dentro del runtime.
            runtime.speech_connection = live_session

            # Mientras enviamos audio, otra tarea escucha
            # las respuestas de Gemini.
            receiver_task = asyncio.create_task(
                self.receive_translations(
                    session_id=session_id,
                    live_session=live_session,
                )
            )

            try:

                while True:

                    chunk = await runtime.audio_queue.get()

                    try:

                        await self.speech_engine.send_live_audio(
                            live_session=live_session,
                            chunk=chunk,
                        )

                    finally:

                        runtime.audio_queue.task_done()

            except asyncio.CancelledError:

                # La sesión está siendo detenida.
                await self.speech_engine.end_live_audio(
                    live_session=live_session
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
    ):
        """
        Consume los eventos de Gemini Live Translate.

        Por ahora los imprimimos para validar el flujo.
        En el siguiente paso estos eventos irán al
        CaptionAssembler y luego al navegador.
        """

        async for event in (
            self.speech_engine.receive_live_translation(
                live_session
            )
        ):

            if event["type"] == "source":

                print(
                    f"[{session_id}] ORIGINAL: "
                    f"{event['text']}",
                    flush=True,
                )

            elif event["type"] == "translation":

                print(
                    f"[{session_id}] TRADUCCIÓN: "
                    f"{event['text']}",
                    flush=True,
                )