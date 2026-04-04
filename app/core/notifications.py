"""
core/notifications.py
----------------------
Connection manager for handling real-time WebSocket notifications.
"""
from typing import List
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        """
        Broadcast a JSON message to all connected clients.
        Example message: {"type": "CREATE", "title": "New Phone", "message": "iPhone 15 added"}
        """
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Handle cases where a connection might have died
                self.active_connections.remove(connection)


# Global instance to be used across routers and controllers
manager = ConnectionManager()
