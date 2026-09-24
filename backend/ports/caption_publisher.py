from abc import ABC, abstractmethod


class CaptionPublisher(ABC):
    """
    Puerto de salida para publicar subtítulos
    a uno o más clientes conectados.
    """

    @abstractmethod
    async def publish(
        self,
        session_id: str,
        payload: dict,
    ) -> None:
        pass