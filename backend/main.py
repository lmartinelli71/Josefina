from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.application.session_manager import SessionManager
from backend.application.streaming_orchestrator import StreamingOrchestrator
from backend.adapters.outbound.gemini_adapter import GeminiAdapter
from backend.adapters.outbound.websocket_caption_publisher import (
    WebSocketCaptionPublisher,
)


app = FastAPI(
    title="Josefina",
    version="0.1.0",
)


# ---------------------------------
# COMPONENTES COMPARTIDOS
# ---------------------------------

session_manager = SessionManager()

speech_engine = GeminiAdapter()

caption_publisher = WebSocketCaptionPublisher()

orchestrator = StreamingOrchestrator(
    session_manager=session_manager,
    speech_engine=speech_engine,
)


# ---------------------------------
# HEALTH
# ---------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "Josefina",
    }


# ---------------------------------
# ENDPOINT TEMPORAL DE PRUEBA
# ---------------------------------

@app.get("/test-caption/{session_id}")
async def test_caption(
    session_id: str,
):
    await caption_publisher.publish(
        session_id=session_id,
        payload={
            "type": "caption",
            "status": "live",
            "text": "Hola desde Josefina",
        },
    )

    return {
        "status": "sent",
        "session_id": session_id,
    }


# ---------------------------------
# WEBSOCKET DE SUBTÍTULOS
# ---------------------------------

@app.websocket("/ws/captions/{session_id}")
async def caption_websocket(
    websocket: WebSocket,
    session_id: str,
):
    await caption_publisher.connect(
        session_id=session_id,
        websocket=websocket,
    )

    try:
        while True:
            await websocket.receive()

    except WebSocketDisconnect:
        caption_publisher.disconnect(
            session_id=session_id,
            websocket=websocket,
        )