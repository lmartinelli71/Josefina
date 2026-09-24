from dataclasses import dataclass
from typing import List


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
    status: str = "READY"