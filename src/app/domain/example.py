from uuid import UUID
from pydantic import BaseModel

class ExampleDTO(BaseModel):
    id: UUID
    name: str
    url: str
    location: str
