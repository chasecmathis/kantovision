import logging

from fastapi import APIRouter

from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """
    Shallow health check for load balancers and uptime monitors.
    Returns 200 when the process is alive; reports database reachability.
    """
    db_status = "ok"
    try:
        get_db().table("teams").select("id").limit(1).execute()
    except Exception:
        logger.warning("Health check: database unreachable")
        db_status = "error"

    overall = "ok" if db_status == "ok" else "degraded"
    return {"status": overall, "database": db_status}


@router.get("/metrics")
def metrics() -> dict:
    """
    Live operational counters — useful for dashboards and alerting.
    Not authenticated; exposes no sensitive data.
    """
    # Import here to avoid circular imports at module load time
    from app.battle.manager import _battles
    from app.battle.matchmaking import _queue
    from app.sockets.caches import _recent_battle_ends
    from app.sockets.connections import manager
    from app.sockets.timers import _move_timeouts, _pending_forfeits

    return {
        "active_battles": len(_battles),
        "queue_depth": len(_queue),
        "active_connections": len(manager._sockets),
        "pending_reconnects": len(_pending_forfeits),
        "pending_move_timeouts": len(_move_timeouts),
        "recent_battle_ends": len(_recent_battle_ends),
    }
