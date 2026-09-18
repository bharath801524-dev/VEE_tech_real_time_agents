"""
MindMesh WebSocket Manager — broadcast messages to all connected clients.
"""
import json
from typing import Set, Dict, Any
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, message: Dict[str, Any]):
        dead = set()
        text = json.dumps(message, default=str)
        for ws in self.active:
            try:
                await ws.send_text(text)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.active.discard(ws)

    @property
    def count(self) -> int:
        return len(self.active)


ws_manager = ConnectionManager()
