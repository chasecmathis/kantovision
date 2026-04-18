from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.database import get_db
from app.dependencies import UserIdDep
from app.schemas import SaveTeamRequest, TeamRow

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("")
def list_teams(user: UserIdDep) -> list[TeamRow]:
    db = get_db()
    result = (
        db.table("teams")
        .select("*")
        .eq("user_id", user.id)
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data


@router.post("", status_code=status.HTTP_201_CREATED)
def create_team(body: SaveTeamRequest, user: UserIdDep) -> TeamRow:
    settings = get_settings()
    db = get_db()
    existing = db.table("teams").select("id").eq("user_id", user.id).execute()
    if len(existing.data) >= settings.max_teams_per_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {settings.max_teams_per_user} teams reached",
        )
    payload = {
        "user_id": user.id,
        "name": body.name,
        "slots": [s.model_dump() if s else None for s in body.slots],
    }
    result = db.table("teams").insert(payload).execute()
    return result.data[0]


@router.put("/{team_id}")
def update_team(team_id: str, body: SaveTeamRequest, user: UserIdDep) -> TeamRow:
    db = get_db()
    existing = (
        db.table("teams")
        .select("id")
        .eq("id", team_id)
        .eq("user_id", user.id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    payload = {
        "name": body.name,
        "slots": [s.model_dump() if s else None for s in body.slots],
    }
    result = (
        db.table("teams")
        .update(payload)
        .eq("id", team_id)
        .eq("user_id", user.id)
        .execute()
    )
    return result.data[0]


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: str, user: UserIdDep) -> None:
    db = get_db()
    existing = (
        db.table("teams")
        .select("id")
        .eq("id", team_id)
        .eq("user_id", user.id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    db.table("teams").delete().eq("id", team_id).eq("user_id", user.id).execute()
