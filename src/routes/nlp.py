import os
import aiofiles
from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from loguru import logger

from helpers.config import get_settings, Settings

from .schemes.data import ProcessRequest

from controllers import DataController, ProjectController, ProcessController

from models import ResponseSignal
from models import AssetTypeEnum


from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.db_schemes.data_chunk import DataChunk
from models.db_schemes.asset import Asset

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["NLP"],
)

