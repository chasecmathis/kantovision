from fastapi import APIRouter

from app.battle.matchmaking import queue_position
from app.database import get_db
from app.dependencies import UserIdDep
from app.schemas import BattleHistoryItem, BattleRow

router = APIRouter(prefix="/battles", tags=["battles"])


@router.get("/queue")
def get_queue_status(user_id: UserIdDep) -> dict:
    uid = getattr(user_id, "id", str(user_id))
    return {"position": queue_position(uid)}


@router.get("/history")
def get_battle_history(user_id: UserIdDep) -> list[BattleHistoryItem]:
    uid = getattr(user_id, "id", str(user_id))
    db = get_db()
    result = (
        db.table("battles")
        .select("*")
        .or_(f"player1_id.eq.{uid},player2_id.eq.{uid}")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    rows = result.data or []
    if not rows:
        return []

    # Collect unique player IDs to look up usernames in a single query
    player_ids = {r["player1_id"] for r in rows} | {r["player2_id"] for r in rows}
    profiles_result = db.table("profiles").select("id,username").in_("id", list(player_ids)).execute()
    username_map: dict[str, str] = {p["id"]: p["username"] for p in (profiles_result.data or [])}

    return [
        BattleHistoryItem(
            **{k: v for k, v in row.items() if k in BattleRow.model_fields},
            player1_username=username_map.get(row["player1_id"]),
            player2_username=username_map.get(row["player2_id"]),
        )
        for row in rows
    ]
