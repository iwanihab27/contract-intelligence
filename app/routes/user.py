import logging
from uuid import UUID
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse

logger = logging.getLogger("contract-rag.users")
router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):

    logger.info(f"Registering user: {user_in.username}")
    query = select(User).where((User.email == user_in.email) | (User.username == user_in.username))
    result = await db.execute(query)
    if result.scalars().first():
        return JSONResponse(status_code=400, content={"message": "User already exists"})

    new_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=user_in.password,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login")
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):

    logger.info(f"Login attempt: {login_data.username}")
    query = select(User).where(User.username == login_data.username)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or user.hashed_password != login_data.password:
        return JSONResponse(status_code=401, content={"message": "Invalid credentials"})

    return JSONResponse(status_code=200, content={
        "message": "Login success",
        "user": {"id": str(user.id), "username": user.username}
    })

@router.get("/{user_id}", response_model=UserResponse)
async def get_profile(user_id: UUID, db: AsyncSession = Depends(get_db)):

    user = await db.get(User, user_id)
    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found"})
    return user

@router.delete("/{user_id}")
async def delete_account(user_id: UUID, db: AsyncSession = Depends(get_db)):

    user = await db.get(User, user_id)
    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found"})
    await db.delete(user)
    await db.commit()
    return JSONResponse(status_code=200, content={"message": "Deleted", "id": str(user_id)})