import logging
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.future import select
from src.models.user import User
from src.core.security import get_password_hash, verify_password, create_access_token
from src.controllers.base_controller import BaseController
from src.enums.user_enums import UserEnums
from fastapi.security import OAuth2PasswordRequestForm

logger = logging.getLogger(__name__)


class UserController(BaseController):

    async def create_user(self, user_in):
        query = select(User).where(
            (User.email == user_in.email) | (User.username == user_in.username)
        )
        result = await self.db.execute(query)
        if result.scalar_one_or_none():
            return False, UserEnums.USER_ALREADY_EXISTS.value

        new_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            is_active=True
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        logger.info(f"User created: {new_user.username}")
        return True, new_user

    async def login(self, username: str, password: str):
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            return False, UserEnums.INVALID_CREDENTIALS.value

        token = create_access_token(subject=user.id)
        logger.info(f"User logged in: {user.username}")
        return True, {"access_token": token, "token_type": "bearer"}

    async def get_user(self, user_id: str):
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            return False, UserEnums.USER_NOT_FOUND.value
        return True, user

    async def delete_user(self, user_id: str):
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            return False, UserEnums.USER_NOT_FOUND.value
        await self.db.delete(user)
        await self.db.commit()
        logger.info(f"User deleted: {user_id}")
        return True, UserEnums.ACCOUNT_DELETED.value