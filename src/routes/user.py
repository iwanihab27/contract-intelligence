import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.config import settings
from src.controllers.user_controller import UserController
from src.schemas.user import UserCreate, UserLogin, UserResponse, TokenRefreshRequest
from fastapi.security import OAuth2PasswordRequestForm
from src.core.limiter import limiter
from fastapi import Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    controller = UserController(db=db, settings=settings)
    success, result = await controller.create_user(user_in)

    if not success:
        return JSONResponse(status_code=400, content={"fail": False, "message": result})

    return {"success": True, "message": "User registered successfully", "user_id": str(result.id)}


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    controller = UserController(db=db, settings=settings)
    success, result = await controller.login(form_data.username, form_data.password)

    if not success:
        return JSONResponse(status_code=401, content={"fail": False, "message": result})

    return {"success": True, **result}


@router.get("/{user_id}", response_model=UserResponse)
@limiter.limit("30/minute")
async def get_profile(request: Request, user_id: str, db: AsyncSession = Depends(get_db)):
    controller = UserController(db=db, settings=settings)
    success, result = await controller.get_user(user_id)

    if not success:
        return JSONResponse(status_code=404, content={"fail": False, "message": result})

    return result


@router.delete("/{user_id}")
@limiter.limit("10/minute")
async def delete_account(request: Request, user_id: str, db: AsyncSession = Depends(get_db)):
    controller = UserController(db=db, settings=settings)
    success, result = await controller.delete_user(user_id)

    if not success:
        return JSONResponse(status_code=404, content={"fail": False, "message": result})

    return {"success": True, "message": result}

@router.post("/refresh")
@limiter.limit("10/minute")
async def refresh_token(request: Request,body: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    controller = UserController(db=db, settings=settings)
    success, result = await controller.refresh_access_token(body.refresh_token)

    if not success:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": result}
        )

    return {"success": True, **result}