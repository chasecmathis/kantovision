from __future__ import annotations

import asyncio

from fastapi import WebSocket


class ConnectionManager:
    """
    Manages WebSocket connections and battle rooms.

    Rooms map battle_id → set of user_ids.
    Sockets map user_id → WebSocket.
    """

    def __init__(self) -> None:
        self._rooms: dict[str, set[str]] = {}
        self._sockets: dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket, user_id: str) -> None:
        self._sockets[user_id] = ws

    async def disconnect(self, user_id: str) -> None:
        self._sockets.pop(user_id, None)
        for members in self._rooms.values():
            members.discard(user_id)

    async def join_room(self, battle_id: str, user_id: str) -> None:
        self._rooms.setdefault(battle_id, set()).add(user_id)

    async def leave_room(self, battle_id: str) -> None:
        self._rooms.pop(battle_id, None)

    async def send_to_user(self, user_id: str, message: dict) -> None:
        ws = self._sockets.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                pass

    async def broadcast_to_room(self, battle_id: str, message: dict) -> None:
        members = set(self._rooms.get(battle_id, set()))
        await asyncio.gather(
            *(self.send_to_user(uid, message) for uid in members),
            return_exceptions=True,
        )


manager = ConnectionManager()
