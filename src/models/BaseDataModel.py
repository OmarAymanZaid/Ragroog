from pymongo.asynchronous.database import AsyncDatabase
from helpers.config import get_settings, Settings

class BaseDataModel:
    """The foundational database access object layer.
    
    Provides all derived child collection models with structural access 
    to the active PyMongo Async database context and global application settings.
    """
    def __init__(self, db_client: AsyncDatabase):
        self.db_client = db_client
        self.app_settings: Settings = get_settings()