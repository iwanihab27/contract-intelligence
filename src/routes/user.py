import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.config import settings
from src.controllers.user_controller import UserController
from src.schemas.user import UserCreate, UserLogin, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    controller = UserController(db=db, settings=settings)
    success, result = await controller.create_user(user_in)

    if not success:
        return JSONResponse(status_code=400, content={"fail": False, "message": result})

    return {"success": True, "message": "User registered successfully", "user_id": str(result.uuid)}


@router.post("/login")
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    controller = UserController(db=db, settings=settings)
    success, result = await controller.login(login_data.username, login_data.password)

    if not success:
        return JSONResponse(status_code=401, content={"fail": False, "message": result})

    return {"success": True, **result}


@router.get("/{user_id}", response_model=UserResponse)
async def get_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    controller = UserController(db=db, settings=settings)
    success, result = await controller.get_user(user_id)

    if not success:
        return JSONResponse(status_code=404, content={"fail": False, "message": result})

    return result


@router.delete("/{user_id}")
async def delete_account(user_id: int, db: AsyncSession = Depends(get_db)):
    controller = UserController(db=db, settings=settings)
    success, result = await controller.delete_user(user_id)

    if not success:
        return JSONResponse(status_code=404, content={"fail": False, "message": result})

    return {"success": True, "message": result}