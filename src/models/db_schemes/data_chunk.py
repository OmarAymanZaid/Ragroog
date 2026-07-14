from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field
from bson import ObjectId
from models.db_schemes.base_types import PyObjectId

class DataChunk(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict[str, Any]
    chunk_order: int = Field(..., gt=0)
    chunk_project_id: PyObjectId
    chunk_asset_id: PyObjectId

    model_config = {
        "arbitrary_types_allowed": True,
        "populate_by_name": True,
    }

    @classmethod
    def get_indexes(cls) -> list[dict[str, Any]]:
        return [
            {
                "key": [("chunk_project_id", 1)],
                "name": "chunk_project_id_index_1",
                "unique": False
            }
        ]
