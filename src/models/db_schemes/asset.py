from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field
from models.db_schemes.base_types import PyObjectId

class Asset(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    asset_project_id: PyObjectId
    asset_type: str = Field(..., min_length=1)
    asset_name: str = Field(..., min_length=1)
    asset_size: Optional[int] = Field(default=None, ge=0)
    asset_config: Optional[dict[str, Any]] = Field(default=None)
    asset_pushed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "arbitrary_types_allowed": True,
        "populate_by_name": True,
    }

    @classmethod
    def get_indexes(cls) -> list[dict[str, Any]]:
        return [
            {
                "key": [("asset_project_id", 1)],
                "name": "asset_project_id_index_1",
                "unique": False
            },
            {
                "key": [
                    ("asset_project_id", 1),
                    ("asset_name", 1)
                ],
                "name": "asset_project_id_name_index_1",
                "unique": True
            },
        ]
