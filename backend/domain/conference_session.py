from dataclasses import dataclass
from enum import Enum
from typing import List


class SessionStatus(str, Enum):
    READY = "READY"
    LIVE = "LIVE"
    CLOSED = "CLOSED"


@dataclass
class ConferenceSession:
    """
    Representa una charla o sesión activa dentro de Josefina.

    Define el idioma de origen, los idiomas habilitados para
    subtítulos y el estado operativo de la sesión.
    """

    id: str
    name: str
    source_language: str
    target_languages: List[str]

    status: SessionStatus = SessionStatus.READY

    producer_connected: bool = False
    viewer_count: int = 0

    def start(self) -> None:
        if self.status == SessionStatus.CLOSED:
            raise ValueError(
                "Una sesión cerrada no puede reiniciarse"
            )

        self.status = SessionStatus.LIVE

    def close(self) -> None:
        self.status = SessionStatus.CLOSED

    def connect_producer(self) -> None:
        if self.producer_connected:
            raise ValueError(
                "Ya existe un productor conectado"
            )

        self.producer_connected = True

    def disconnect_producer(self) -> None:
        self.producer_connected = False

    def add_viewer(self) -> None:
        self.viewer_count += 1

    def remove_viewer(self) -> None:
        if self.viewer_count > 0:
            self.viewer_count -= 1