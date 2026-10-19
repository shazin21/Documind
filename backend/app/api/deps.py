from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

# Re-export get_db for route dependency injection
__all__ = ["get_db"]
