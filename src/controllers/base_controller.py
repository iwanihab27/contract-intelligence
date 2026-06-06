import hashlib
import secrets
import os

class BaseController:
    MB = 1024 * 1024

    def __init__(self, db, settings):
        self.db = db
        self.settings = settings

    def generate_hash(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        return f"{hashlib.sha256(secrets.token_bytes(32)).hexdigest()[:16]}{ext}"