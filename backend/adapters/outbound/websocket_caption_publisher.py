from collections import defaultdict

from fastapi import WebSocket

from backend.ports.caption_publisher import CaptionPublisher


class WebSocketCaptionPublisher(CaptionPublisher):
    """
    Publica subtítulos a todos los navegadores
    conectados a una sesión determinada.
    """

    def __init__(self):
        self.connections = defaultdict(set)

    async def connect(
        self,
        session_id: str,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()
        self.connections[session_id].add(websocket)

    def disconnect(
        self,
        session_id: str,
        websocket: WebSocket,
    ) -> None:
        session_connections = self.connections.get(
            session_id
        )

        if not session_connections:
            return

        session_connections.discard(websocket)

        if not session_connections:
            self.connections.pop(
                session_id,
                None,
            )

    async def publish(
        self,
        session_id: str,
        payload: dict,
    ) -> None:
        session_connections = list(
            self.connections.get(
                session_id,
                set(),
            )
        )

        disconnected = []

        for websocket in session_connections:
            try:
                await websocket.send_json(
                    payload
                )

            except Exception:
                disconnected.append(
                    websocket
                )

        for websocket in disconnected:
            self.disconnect(
                session_id=session_id,
                websocket=websocket,
            )