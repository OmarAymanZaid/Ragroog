from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, GetCoreSchemaHandler
from bson import ObjectId
from models.db_schemes.base_types import PyObjectId

class Project(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    project_id: str = Field(..., min_length=1)

    model_config = {
        "arbitrary_types_allowed": True,
        "populate_by_name": True,  # Replaces allow_population_by_field_name
    }

    @field_validator('project_id')
    @classmethod
    def validate_project_id(cls, value: str) -> str:
        if not value.isalnum():
            raise ValueError('project_id must be alphanumeric')
        return value

    @classmethod
    def get_indexes(cls) -> list[dict[str, Any]]:
        return [
            {
                "key": [("project_id", 1)],
                "name": "project_id_index_1",
                "unique": True
            }
        ]
