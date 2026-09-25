from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class SpeechEngine(ABC):
    """
    Puerto de salida para cualquier motor de speech
    que procese audio en streaming y produzca traducciones.
    """

    @abstractmethod
    def live_translate_connection(
        self,
        target_language: str,
    ):
        pass

    @abstractmethod
    async def send_live_audio(
        self,
        live_session: Any,
        chunk: bytes,
        sample_rate: int = 16000,
    ) -> None:
        pass

    @abstractmethod
    def receive_live_translation(
        self,
        live_session: Any,
    ) -> AsyncIterator[dict]:
        pass

    @abstractmethod
    async def end_live_audio(
        self,
        live_session: Any,
    ) -> None:
        pass