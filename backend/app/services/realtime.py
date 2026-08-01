from fastapi import WebSocket

class RealtimeHub:
    def __init__(self): self.connections: dict[WebSocket, int] = {}
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept(); self.connections[websocket] = user_id
    def disconnect(self, websocket: WebSocket): self.connections.pop(websocket, None)
    @property
    def active_count(self) -> int: return len(self.connections)
    async def publish(self, user_id: int, payload: dict):
        stale: list[WebSocket] = []
        for connection, owner_id in self.connections.items():
            if owner_id != user_id: continue
            try: await connection.send_json(payload)
            except Exception: stale.append(connection)
        for connection in stale: self.disconnect(connection)

hub = RealtimeHub()
