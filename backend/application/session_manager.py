import asyncio
from typing import Dict

from backend.domain.conference_session import (
    ConferenceSession,
)
from backend.application.session_runtime import (
    SessionRuntime,
)


class SessionManager:
    """
    Administra las ConferenceSession desde el punto
    de vista operativo.

    Mantiene la relación entre el dominio
    ConferenceSession y los recursos técnicos
    asociados en SessionRuntime.
    """

    def __init__(self):
        self.sessions: Dict[
            str,
            ConferenceSession,
        ] = {}

        self.runtimes: Dict[
            str,
            SessionRuntime,
        ] = {}

    # ---------------------------------
    # CREAR SESIÓN
    # ---------------------------------

    def create_session(
        self,
        session_id: str,
        name: str,
        source_language: str,
        target_languages: list[str],
    ) -> ConferenceSession:

        session = ConferenceSession(
            id=session_id,
            name=name,
            source_language=source_language,
            target_languages=target_languages,
        )

        self.sessions[session_id] = session

        return session

    # ---------------------------------
    # CONSULTAR SESIÓN
    # ---------------------------------

    def get_session(
        self,
        session_id: str,
    ) -> ConferenceSession:

        return self.sessions[session_id]

    def list_sessions(
        self,
    ) -> list[ConferenceSession]:

        return list(
            self.sessions.values()
        )

    # ---------------------------------
    # INICIAR SESIÓN
    # ---------------------------------

    def start_session(
        self,
        session_id: str,
    ) -> SessionRuntime:

        session = self.get_session(
            session_id
        )

        # Si ya existe runtime,
        # no creamos otro.
        if session_id in self.runtimes:
            return self.runtimes[
                session_id
            ]

        runtime = SessionRuntime(
            session_id=session_id,
            audio_queue=asyncio.Queue(),
        )

        self.runtimes[
            session_id
        ] = runtime

        session.start()

        return runtime

    # ---------------------------------
    # CERRAR SESIÓN
    # ---------------------------------

    def stop_session(
        self,
        session_id: str,
    ) -> None:

        session = self.get_session(
            session_id
        )

        session.close()

        self.runtimes.pop(
            session_id,
            None,
        )

    # ---------------------------------
    # PRODUCTOR
    # ---------------------------------

    def connect_producer(
        self,
        session_id: str,
    ) -> None:

        session = self.get_session(
            session_id
        )

        session.connect_producer()

    def disconnect_producer(
        self,
        session_id: str,
    ) -> None:

        session = self.get_session(
            session_id
        )

        session.disconnect_producer()

    # ---------------------------------
    # VIEWERS
    # ---------------------------------

    def add_viewer(
        self,
        session_id: str,
    ) -> None:

        session = self.get_session(
            session_id
        )

        session.add_viewer()

    def remove_viewer(
        self,
        session_id: str,
    ) -> None:

        session = self.get_session(
            session_id
        )

        session.remove_viewer()

    # ---------------------------------
    # RUNTIME
    # ---------------------------------

    def get_runtime(
        self,
        session_id: str,
    ) -> SessionRuntime:

        return self.runtimes[
            session_id
        ]