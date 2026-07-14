from typing import Any
from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler
from bson import ObjectId

class PyObjectId(ObjectId):
    """Custom type wrapper enabling seamless Pydantic v2 validation for BSON ObjectIds."""
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.is_instance_schema(ObjectId),
            serialization=core_schema.plain_serializer_function_macro(lambda x: str(x)),
        )