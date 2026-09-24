from abc import ABC, abstractmethod

from backend.domain.conference_session import ConferenceSession


class SpeechEngine(ABC):
    """
    Define el contrato que debe cumplir cualquier motor de speech
    utilizado por Josefina.

    La capa de aplicación depende de esta interfaz y no de una
    implementación concreta como Gemini.
    """

    @abstractmethod
    async def send_audio(
        self,
        session: ConferenceSession,
        chunk: bytes,
    ) -> None:
        """
        Recibe un chunk de audio asociado a una sesión activa.
        """
        pass