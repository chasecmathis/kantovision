from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_db

_security = HTTPBearer()


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_security)],
) -> str:
    user_response = get_db().auth.get_user(credentials.credentials)
    if not user_response.user:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user_response.user


UserIdDep = Annotated[str, Depends(get_current_user_id)]
