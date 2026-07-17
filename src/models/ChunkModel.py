from typing import Any
from bson import ObjectId
from pymongo import InsertOne
from pymongo.asynchronous.database import AsyncDatabase

from . import ChunkModel
from .db_schemes.data_chunk import DataChunk
from .enums.DatabaseEnums import DataBaseEnum


class ChunkModel:
    def __init__(self, db_client: AsyncDatabase):
        self.db_client = db_client
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]

    @classmethod
    async def create_instance(cls, db_client: AsyncDatabase) -> ChunkModel:
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    async def init_collection(self) -> None:
        all_collections = await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_CHUNK_NAME.value not in all_collections:
            indexes = DataChunk.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def create_chunk(self, chunk: DataChunk) -> DataChunk:
        document_data = chunk.model_dump(by_alias=True, exclude_unset=True)
        result = await self.collection.insert_one(document_data)
        chunk.id = result.inserted_id
        return chunk

    async def get_chunk(self, chunk_id: str) -> DataChunk | None:
        # Explicit validation and mapping to native BSON ObjectId
        if not ObjectId.is_valid(chunk_id):
            return None

        result = await self.collection.find_one({"_id": ObjectId(chunk_id)})
        return DataChunk(**result) if result else None

    async def insert_many_chunks(self, chunks: list[DataChunk], batch_size: int = 100) -> int:
        """Executes batched bulk write operations via PyMongo Async."""
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]

            operations = [
                InsertOne(chunk.model_dump(by_alias=True, exclude_unset=True))
                for chunk in batch
            ]

            # Native PyMongo Async handles standard bulk_write perfectly
            await self.collection.bulk_write(operations)

        return len(chunks)

    async def delete_chunks_by_project_id(self, project_id: ObjectId) -> int:
        result = await self.collection.delete_many({"chunk_project_id": project_id})
        return result.deleted_count
    
    async def get_project_chunks(
        self, 
        project_id: ObjectId, 
        page_no: int = 1, 
        page_size: int = 50
    ) -> list[DataChunk]:
        # Query matching 'chunk_project_id' with pagination skip and limit
        cursor = (
            self.collection.find({"chunk_project_id": project_id})
            .skip((page_no - 1) * page_size)
            .limit(page_size)
        )

        chunks = []
        # Modern PyMongo Async allows streaming documents directly via async iteration
        async for document in cursor:
            chunks.append(DataChunk(**document))
            
        return chunks

    async def get_total_chunks_count(self, project_id: ObjectId) -> int:
        # High-performance native document counting matching the query criteria
        return await self.collection.count_documents({"chunk_project_id": project_id})
    