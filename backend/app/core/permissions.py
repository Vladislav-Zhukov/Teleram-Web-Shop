from fastapi import HTTPException
from app.db.models.user import User

def require_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
