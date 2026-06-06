from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.future import select
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from base_controller import BaseController

class UserController(BaseController):
    async def create_user(self, user_in):
        query = select(User).where(User.email == user_in.email)
        result = await self.db.execute(query)
        if result.scalar_one_or_none():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "message": "Email already registered"}
            )

        hashed_pw = get_password_hash(user_in.password)

        new_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_pw
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return {"success": True, "message": "User created successfully", "user_id": new_user.id}

    async def login(self, email: str, password: str):
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"success": False, "message": "Invalid email or password"}
            )

        token = create_access_token(subject=user.id)

        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer"
        }

    async def delete_user(self, user_id: int):
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "Cannot delete: User not found"}
            )

        await self.db.delete(user)
        await self.db.commit()
        return {"success": True, "message": "Account deleted"}