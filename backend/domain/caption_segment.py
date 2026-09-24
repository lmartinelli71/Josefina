from dataclasses import dataclass
from typing import Dict


@dataclass
class CaptionSegment:
    """
    Representa un fragmento temporal de subtítulos generado
    durante una ConferenceSession.

    texts contiene las versiones del fragmento por idioma.
    """

    session_id: str
    start_time: float
    end_time: float
    texts: Dict[str, str]