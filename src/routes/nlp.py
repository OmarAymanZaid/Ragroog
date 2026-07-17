from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from loguru import logger

from helpers.config import get_settings, Settings

from routes.schemes.nlp import PushRequest, SearchRequest

from controllers import NLPController

from models import ResponseSignal
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel

from tqdm.auto import tqdm

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["NLP"],
)

