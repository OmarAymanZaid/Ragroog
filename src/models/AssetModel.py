from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from . import AssetModel
from .BaseDataModel import BaseDataModel
from .db_schemes.asset import Asset
from .enums.DatabaseEnums import DataBaseEnum


class AssetModel(BaseDataModel):
    def __init__(self, db_client: AsyncDatabase):
        # Explicit type hinting cascades perfectly from BaseDataModel
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_ASSET_NAME.value]

    @classmethod
    async def create_instance(cls, db_client: AsyncDatabase) -> AssetModel:
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    async def init_collection(self) -> None:
        all_collections = await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_ASSET_NAME.value not in all_collections:
            indexes = Asset.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def create_asset(self, asset: Asset) -> Asset:
        document_data = asset.model_dump(by_alias=True, exclude_unset=True)
        result = await self.collection.insert_one(document_data)
        asset.id = result.inserted_id
        return asset

    async def get_all_project_assets(self, asset_project_id: str | ObjectId, asset_type: str) -> list[Asset]:
        # Normalize incoming criteria to strict BSON ObjectId formats cleanly
        project_id_bson = ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id

        cursor = self.collection.find({
            "asset_project_id": project_id_bson,
            "asset_type": asset_type,
        })

        assets = []
        async for document in cursor:
            assets.append(Asset(**document))
            
        return assets

    async def get_asset_record(self, asset_project_id: str | ObjectId, asset_name: str) -> Asset | None:
        project_id_bson = ObjectId(asset_project_id) if isinstance(asset_project_id, str) else asset_project_id

        record = await self.collection.find_one({
            "asset_project_id": project_id_bson,
            "asset_name": asset_name,
        })

        return Asset(**record) if record else None