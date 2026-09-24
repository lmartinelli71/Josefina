import asyncio
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class SessionRuntime:
    """
    Representa los recursos técnicos que existen mientras
    una ConferenceSession está activa.

    No forma parte del dominio: contiene elementos de ejecución
    como la cola FIFO de audio, la tarea consumidora y la conexión
    con el motor de speech.
    """

    session_id: str
    audio_queue: asyncio.Queue
    consumer_task: Optional[asyncio.Task] = None
    speech_connection: Optional[Any] = None