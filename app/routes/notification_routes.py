"""
routes/notification_routes.py
------------------------------
WebSocket endpoint for real-time notifications.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.notifications import manager

router = APIRouter(tags=["🔔 Real-time Notifications"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection open - listen for client-sent data (if needed)
            data = await websocket.receive_text()
            # Respond or ignore data from client
            await manager.send_personal_message(f"Message received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Error in WebSocket: {e}")
        manager.disconnect(websocket)
