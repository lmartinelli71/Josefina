from backend.application.session_manager import SessionManager


class StreamingOrchestrator:
    """
    Coordina el flujo de audio de una sesión activa.

    Consume los chunks desde la cola FIFO del SessionRuntime
    y los envía al motor de speech configurado.
    """

    def __init__(self, session_manager: SessionManager, speech_engine):
        self.session_manager = session_manager
        self.speech_engine = speech_engine

    async def consume_audio(self, session_id: str):
        """
        Consume continuamente audio de la cola FIFO de una sesión.
        """

        runtime = self.session_manager.get_runtime(session_id)

        while True:
            chunk = await runtime.audio_queue.get()

            try:
                await self.send_audio_to_engine(
                    session_id=session_id,
                    chunk=chunk,
                )
            finally:
                runtime.audio_queue.task_done()

    async def send_audio_to_engine(self, session_id: str, chunk: bytes):
        """
        Envía un chunk de audio al motor de speech.
        """

        session = self.session_manager.get_session(session_id)

        await self.speech_engine.send_audio(
            session=session,
            chunk=chunk,
        )