import asyncio
from typing import Dict

from backend.domain.conference_session import ConferenceSession
from backend.application.session_runtime import SessionRuntime


class SessionManager:
    """
    Administra las ConferenceSession desde el punto de vista operativo.

    Permite crear, consultar, listar, iniciar y detener sesiones.
    También mantiene la relación entre cada ConferenceSession y
    los recursos técnicos asociados en SessionRuntime.
    """

    def __init__(self):
        self.sessions: Dict[str, ConferenceSession] = {}
        self.runtimes: Dict[str, SessionRuntime] = {}

    def create_session(
        self,
        session_id: str,
        name: str,
        source_language: str,
        target_languages: list[str],
    ) -> ConferenceSession:
        """
        Crea una nueva sesión en estado READY.
        """

        session = ConferenceSession(
            id=session_id,
            name=name,
            source_language=source_language,
            target_languages=target_languages,
            status="READY",
        )

        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> ConferenceSession:
        """
        Devuelve una sesión existente.
        """

        return self.sessions[session_id]

    def list_sessions(self) -> list[ConferenceSession]:
        """
        Devuelve todas las sesiones registradas.
        """

        return list(self.sessions.values())

    def start_session(self, session_id: str) -> SessionRuntime:
        """
        Inicia una sesión y crea sus recursos técnicos de ejecución.
        """

        session = self.get_session(session_id)

        runtime = SessionRuntime(
            session_id=session_id,
            audio_queue=asyncio.Queue(),
        )

        self.runtimes[session_id] = runtime
        session.status = "LIVE"

        return runtime

    def stop_session(self, session_id: str) -> None:
        """
        Detiene una sesión.
        """

        session = self.get_session(session_id)
        session.status = "STOPPED"

        self.runtimes.pop(session_id, None)

    def get_runtime(self, session_id: str) -> SessionRuntime:
        """
        Devuelve el runtime asociado a una sesión activa.
        """

        return self.runtimes[session_id]