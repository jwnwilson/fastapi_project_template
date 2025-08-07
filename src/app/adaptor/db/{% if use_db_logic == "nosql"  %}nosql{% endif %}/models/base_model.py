import uuid
from abc import ABC
from datetime import datetime

from pydantic import BaseModel


# Base model for all tables in all projects
class Base(BaseModel, ABC):
    """Base for all models."""

    id: uuid.UUID
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
