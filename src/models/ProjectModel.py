from typing import Any
from pymongo.asynchronous.database import AsyncDatabase

from . import ProjectModel
from .db_schemes.project import Project
from .enums.DatabaseEnums import DataBaseEnum

class ProjectModel:
    def __init__(self, db_client: AsyncDatabase):
        self.db_client = db_client
        self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]

    @classmethod
    async def create_instance(cls, db_client: AsyncDatabase) -> ProjectModel:
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    async def init_collection(self) -> None:
        all_collections = await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_PROJECT_NAME.value not in all_collections:
            # Create indexes safely
            indexes = Project.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name=index["name"],
                    unique=index["unique"]
                )

    async def create_project(self, project: Project) -> Project:
        # Convert to dictionary using v2 syntax
        document_data = project.model_dump(by_alias=True, exclude_unset=True)
        
        result = await self.collection.insert_one(document_data)
        project.id = result.inserted_id
        return project

    async def get_project_or_create_one(self, project_id: str) -> Project:
        record = await self.collection.find_one({"project_id": project_id})

        if record is None:
            project = Project(project_id=project_id)
            project = await self.create_project(project=project)
            return project
        
        return Project(**record)

    async def get_all_projects(self, page: int = 1, page_size: int = 10) -> tuple[list[Project], int]:
        total_documents = await self.collection.count_documents({})

        # Calculate pagination limits
        total_pages = total_documents // page_size
        if total_documents % page_size > 0:
            total_pages += 1

        # Execute query using PyMongo Async syntax
        cursor = self.collection.find().skip((page - 1) * page_size).limit(page_size)
        
        projects = []
        # Modern PyMongo Async allows streaming documents directly via async iteration loop
        async for document in cursor:
            projects.append(Project(**document))

        return projects, total_pages