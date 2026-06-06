import os
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.base_controller import BaseController
from app.core.config import Settings
from app.enums import FileEnums, ResponseEnums, ContractEnums
from app.models.contract import Contract


class UploadController(BaseController):
    def __init__(self, db: AsyncSession, settings: Settings):
        super().__init__(db, settings)

    def validate_file(self, file: UploadFile):
        ext = os.path.splitext(file.filename)[1].lower()
        file.file.seek(0, 2)
        size_mb = file.file.tell() / self.MB
        file.file.seek(0)

        if ext not in [e.value for e in FileEnums]:
            return False, ResponseEnums.FILE_TYPE_NOT_SUPPORTED.value

        if size_mb == 0:
            return False, ResponseEnums.FILE_NOT_FOUND.value

        if size_mb > self.settings.MAX_FILE_SIZE_MB:
            return False, ResponseEnums.FILE_SIZE_TOO_LARGE.value

        return True, ResponseEnums.FILE_UPLOAD_SUCCESS.value

    async def save_file(self, file: UploadFile):
        ext = os.path.splitext(file.filename)[1].lower()  # splits the id from the ext
        unique_name = self.generate_hash(file.filename)  # gets the file ext .pdf
        file_path = os.path.join(self.settings.UPLOAD_DIR, unique_name)
        os.makedirs(self.settings.UPLOAD_DIR, exist_ok=True)

        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        return unique_name, file_path

    async def create_contract(self, name: str, file_name: str, file_path: str):
        contract = Contract(name=name, file_name=file_name, file_path=file_path, contract_type=ContractEnums.OTHER)
        self.db.add(contract)
        await self.db.commit()
        await self.db.refresh(contract)
        return contract