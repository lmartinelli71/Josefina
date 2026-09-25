from dataclasses import dataclass
from enum import Enum
from typing import Dict


class CaptionStatus(str, Enum):
    LIVE = "LIVE"
    CLOSED = "CLOSED"


@dataclass
class CaptionSegment:
    """
    Representa un fragmento temporal de subtítulos generado
    durante una ConferenceSession.

    texts contiene las versiones del fragmento por idioma.
    """

    session_id: str
    start_time: float
    texts: Dict[str, str]

    end_time: float | None = None
    status: CaptionStatus = CaptionStatus.LIVE

    def update_text(
        self,
        language: str,
        text: str,
    ) -> None:
        self.texts[language] = text

    def close(
        self,
        end_time: float,
    ) -> None:
        self.end_time = end_time
        self.status = CaptionStatus.CLOSED