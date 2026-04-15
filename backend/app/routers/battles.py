from fastapi import APIRouter

from app.battle.matchmaking import queue_position
from app.database import get_db
from app.dependencies import UserIdDep
from app.schemas import BattleRow

router = APIRouter(prefix="/battles", tags=["battles"])


@router.get("/queue")
def get_queue_status(user_id: UserIdDep) -> dict:
    uid = getattr(user_id, "id", str(user_id))
    return {"position": queue_position(uid)}


@router.get("/history")
def get_battle_history(user_id: UserIdDep) -> list[BattleRow]:
    uid = getattr(user_id, "id", str(user_id))
    result = (
        get_db()
        .table("battles")
        .select("*")
        .or_(f"player1_id.eq.{uid},player2_id.eq.{uid}")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    return [BattleRow(**row) for row in (result.data or [])]
