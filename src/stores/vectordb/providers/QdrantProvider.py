from qdrant_client import models, QdrantClient
from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums
from loguru import logger
from models.db_schemes import RetrievedDocument
import uuid

class QdrantDBProvider(VectorDBInterface):

    def __init__(self, db_client: str, default_vector_size: int = 786,
                 distance_method: str = None, index_threshold: int = 100):

        self.client = None
        self.db_client = db_client
        self.distance_method = None
        self.default_vector_size = default_vector_size

        if distance_method == DistanceMethodEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMethodEnums.DOT.value:
            self.distance_method = models.Distance.DOT

    async def connect(self):
        self.client = QdrantClient(path=self.db_client)

    async def disconnect(self):
        self.client = None

    async def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)
    
    async def list_all_collections(self) -> list:
        return self.client.get_collections()
    
    async def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)
    
    async def delete_collection(self, collection_name: str):
        # FIX: Added await here
        if await self.is_collection_existed(collection_name):
            logger.info(f"Deleting collection: {collection_name}")
            return self.client.delete_collection(collection_name=collection_name)
        
    async def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        if do_reset:
            # FIX: Added await here
            await self.delete_collection(collection_name=collection_name)
        
        # FIX: Added await here
        if not await self.is_collection_existed(collection_name):
            logger.info(f"Creating new Qdrant collection: {collection_name}")
            
            _ = self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=self.distance_method
                )
            )
            return True
        
        return False
    
    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, record_id: str = None):
        
        if not await self.is_collection_existed(collection_name):
            logger.error(f"Cannot insert new record into non-existent collection: {collection_name}")
            return False
        
        try:
            # Inline convert the MongoDB hex string to a valid UUID format for Qdrant
            qdrant_safe_id = str(uuid.UUID(hex=record_id.zfill(32))) if record_id else None

            _ = self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=qdrant_safe_id,
                        vector=vector,
                        payload={
                            "text": text, "metadata": metadata
                        }
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Error while inserting batch: {e}")
            return False

        return True
    
    async def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        
        if metadata is None:
            metadata = [None] * len(texts)

        if record_ids is None:
            record_ids = list(range(0, len(texts)))

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size

            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]

            # Inline convert each MongoDB hex string to a valid UUID format for Qdrant
            batch_records = [
                models.PointStruct(
                    id=str(uuid.UUID(hex=str(batch_record_ids[x]).zfill(32))),
                    vector=batch_vectors[x],
                    payload={
                        "text": batch_texts[x], "metadata": batch_metadata[x]
                    }
                )
                for x in range(len(batch_texts))
            ]

            try:
                _ = self.client.upsert(
                    collection_name=collection_name,
                    points=batch_records,
                )
            except Exception as e:
                logger.error(f"Error while inserting batch: {e}")
                return False

        return True
        
    async def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):
            # Switched from self.client.search to self.client.query_points
            results = self.client.query_points(
                collection_name=collection_name,
                query=vector,  # In query_points, the parameter is 'query', not 'query_vector'
                limit=limit
            ).points  # .points extracts the list of scored points from the response object

            if not results or len(results) == 0:
                return None
            
            return [
                RetrievedDocument(**{
                    "score": result.score,
                    "text": result.payload["text"],
                })
                for result in results
            ]