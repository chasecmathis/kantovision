"""WebSocket battle endpoint and ticket exchange."""

from __future__ import annotations

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.battle.manager import get_battle_by_user
from app.battle.matchmaking import is_queued
from app.battle.state import BattleStatus
from app.dependencies import UserIdDep
from app.sockets.caches import pop_recent_battle_end
from app.sockets.connections import manager
from app.sockets.handlers import (
    handle_disconnect,
    handle_forfeit,
    handle_join_queue,
    handle_leave_queue,
    handle_make_action,
    handle_select_lead,
    handle_submit_switch,
)
from app.sockets.message_types import (
    MSG_BATTLE_END,
    MSG_BATTLE_RESUMED,
    MSG_BATTLE_START,
    MSG_ERROR,
    MSG_FORFEIT,
    MSG_JOIN_QUEUE,
    MSG_LEAVE_QUEUE,
    MSG_MAKE_ACTION,
    MSG_OPPONENT_RECONNECTED,
    MSG_QUEUE_JOINED,
    MSG_SELECT_LEAD,
    MSG_SUBMIT_SWITCH,
    MSG_TEAM_PREVIEW,
)
from app.sockets.rate_limiter import clear_user, is_rate_limited
from app.sockets.serializers import serialize_battle_state
from app.sockets.tickets import consume_ticket, issue_ticket
from app.sockets.timers import cancel_grace_period, get_turn_started_at, opponent_id

logger = logging.getLogger(__name__)
router = APIRouter(tags=["battle-ws"])


# ─── Ticket endpoint ────────────────────────────────────────────────────────


@router.post("/ws/ticket")
async def create_ws_ticket(user: UserIdDep) -> dict:
    """
    Exchange a valid JWT (via Authorization header) for a short-lived WebSocket ticket.
    The ticket is single-use and expires in 30 seconds.
    """
    return {"ticket": issue_ticket(user)}


# ─── WebSocket endpoint ─────────────────────────────────────────────────────


@router.websocket("/ws/battle")
async def battle_ws(
    ws: WebSocket,
    ticket: Annotated[str, Query()],
) -> None:
    # Validate the single-use ticket — no JWT in the URL
    user_id = consume_ticket(ticket)
    if not user_id:
        await ws.close(code=4001, reason="Invalid or expired ticket")
        return

    await ws.accept()
    await manager.connect(ws, user_id)
    logger.info("WebSocket connected: user_id=%s", user_id)

    # Cancel any pending forfeit from a prior disconnect
    pending_forfeit = cancel_grace_period(user_id)

    # Re-join any in-progress battle or restore queue state
    existing = get_battle_by_user(user_id)
    if existing:
        await manager.join_room(existing.id, user_id)
        if pending_forfeit:
            pending_forfeit.cancel()
            # Reconnect: notify opponent and send current state
            logger.info("User reconnected to battle: user_id=%s battle_id=%s", user_id, existing.id)
            await manager.send_to_user(
                opponent_id(existing, user_id),
                {
                    "type": MSG_OPPONENT_RECONNECTED,
                },
            )
            await manager.send_to_user(
                user_id,
                {
                    "type": MSG_BATTLE_RESUMED,
                    "battle_id": existing.id,
                    "state": serialize_battle_state(existing),
                    "turn_started_at": get_turn_started_at(existing.id) or time.time(),
                },
            )
        else:
            # Fresh connect with an existing battle (e.g. page refresh mid-match)
            if existing.status == BattleStatus.TEAM_PREVIEW:
                await manager.send_to_user(
                    user_id,
                    {
                        "type": MSG_TEAM_PREVIEW,
                        "battle_id": existing.id,
                        "state": serialize_battle_state(existing),
                    },
                )
            else:
                await manager.send_to_user(
                    user_id,
                    {
                        "type": MSG_BATTLE_START,
                        "battle_id": existing.id,
                        "state": serialize_battle_state(existing),
                        "turn_started_at": get_turn_started_at(existing.id) or time.time(),
                    },
                )
    else:
        recent_end = pop_recent_battle_end(user_id)
        if recent_end:
            # Battle ended while user was away — show them the result
            await manager.send_to_user(
                user_id,
                {
                    "type": MSG_BATTLE_END,
                    "winner_id": recent_end["winner_id"],
                    "reason": recent_end["reason"],
                },
            )
        elif is_queued(user_id):
            # User navigated away while in queue — restore queue state
            await manager.send_to_user(user_id, {"type": MSG_QUEUE_JOINED})

    try:
        while True:
            try:
                data = await ws.receive_json()
            except Exception:
                break

            if is_rate_limited(user_id):
                logger.warning("Rate limit exceeded for user_id=%s — closing connection", user_id)
                await ws.close(code=4029, reason="Too many messages")
                break

            msg_type = data.get("type")
            if msg_type == MSG_JOIN_QUEUE:
                await handle_join_queue(user_id, data)
            elif msg_type == MSG_LEAVE_QUEUE:
                await handle_leave_queue(user_id)
            elif msg_type == MSG_MAKE_ACTION:
                await handle_make_action(user_id, data)
            elif msg_type == MSG_FORFEIT:
                await handle_forfeit(user_id, data)
            elif msg_type == MSG_SELECT_LEAD:
                await handle_select_lead(user_id, data)
            elif msg_type == MSG_SUBMIT_SWITCH:
                await handle_submit_switch(user_id, data)
            else:
                await manager.send_to_user(
                    user_id,
                    {
                        "type": MSG_ERROR,
                        "message": f"Unknown message type: {msg_type!r}",
                    },
                )
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(user_id)
        await handle_disconnect(user_id)
        clear_user(user_id)
        logger.info("WebSocket disconnected: user_id=%s", user_id)
