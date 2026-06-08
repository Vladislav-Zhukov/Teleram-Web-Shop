from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_redis
from app.schemas.auth import LoginIn, RefreshTokenIn, RegisterIn, TokenPairOut
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(data: RegisterIn, db: AsyncSession = Depends(get_db)):
    user = await AuthService(db).register(data.email, data.password)
    return {"id": user.id, "email": user.email}


@router.post("/login", response_model=TokenPairOut)
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)):
    access, refresh = await AuthService(db).login(data.email, data.password)
    return TokenPairOut(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPairOut)
async def refresh(data: RefreshTokenIn, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    access, refresh_token = await AuthService(db).refresh(data.refresh_token, redis=redis)
    return TokenPairOut(access_token=access, refresh_token=refresh_token)


@router.post("/logout")
async def logout(data: RefreshTokenIn, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    await AuthService(db).logout(data.refresh_token, redis=redis)
    return {"ok": True}
