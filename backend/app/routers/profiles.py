from fastapi import APIRouter, HTTPException, status

from app.database import get_db
from app.dependencies import UserIdDep
from app.schemas import CreateProfileRequest, ProfileRow, UpdateProfileRequest

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me")
def get_my_profile(user: UserIdDep) -> ProfileRow:
    db = get_db()
    result = db.table("profiles").select("*").eq("id", user.id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return result.data[0]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_profile(body: CreateProfileRequest, user: UserIdDep) -> ProfileRow:
    db = get_db()
    existing = db.table("profiles").select("id").eq("id", user.id).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Profile already exists"
        )
    try:
        result = db.table("profiles").insert({
            "id": user.id,
            "username": body.username,
            "display_name": body.display_name,
        }).execute()
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "unique" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        raise
    return result.data[0]


@router.patch("/me")
def update_profile(body: UpdateProfileRequest, user: UserIdDep) -> ProfileRow:
    db = get_db()
    result = (
        db.table("profiles")
        .update({"display_name": body.display_name})
        .eq("id", user.id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return result.data[0]


@router.get("")
def search_profiles(user: UserIdDep, username: str = "") -> list[ProfileRow]:
    if not username.strip():
        return []
    db = get_db()
    result = (
        db.table("profiles")
        .select("*")
        .ilike("username", f"%{username}%")
        .neq("id", user.id)
        .limit(10)
        .execute()
    )
    return result.data


@router.get("/{username}")
def get_profile_by_username(username: str, user: UserIdDep) -> ProfileRow:
    db = get_db()
    result = db.table("profiles").select("*").eq("username", username).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return result.data[0]
