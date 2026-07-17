import os
import aiofiles
from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from loguru import logger

from helpers.config import get_settings, Settings

from .schemes.data import ProcessRequest

from controllers import DataController, ProjectController, ProcessController, NLPController


from models import ResponseSignal
from models import AssetTypeEnum


from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.db_schemes.data_chunk import DataChunk
from models.db_schemes.asset import Asset


data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["Data Management"],
)

@data_router.post("/upload/{project_id}", status_code=status.HTTP_201_CREATED)
async def upload_data(
    request: Request, 
    project_id: str, 
    file: UploadFile,
    app_settings: Settings = Depends(get_settings)
) -> JSONResponse:
    
    """Validates, streams, and saves an incoming data file asset to local storage

    and registers its record entry inside MongoDB.
    """
    
    # 1. Access the modern PyMongo Async DB reference pool cleanly
    db_context = request.app.db
        
    project_model = await ProjectModel.create_instance(db_client=db_context)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    # 2. File Validation Processing
    data_controller = DataController()
    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        logger.warning(f"File validation rejected for project [{project_id}]: {result_signal}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": result_signal}
        )

    # 3. Path Calculations and Streaming
    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename if file.filename else "unnamed",
        project_id=project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as exc:
        logger.error(f"IO Write streaming operation failed on project file storage: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"signal": ResponseSignal.FILE_UPLOAD_FAILED.value}
        )
    finally:
        await file.close()

    # 4. Storage Audit Tracking via MongoDB
    asset_model = await AssetModel.create_instance(db_client=db_context)
    
    asset_resource = Asset(
        asset_project_id=project.id,  # Uses your safe Pydantic v2 PyObjectId mappings
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)
    )

    asset_record = await asset_model.create_asset(asset=asset_resource)

    logger.info(f"Asset record [{asset_record.id}] stored safely for project [{project_id}]")
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_id": str(asset_record.id),
        }
    )

@data_router.post("/process/{project_id}", status_code=status.HTTP_200_OK)
async def process_endpoint(
    request: Request, 
    project_id: str, 
    process_request: ProcessRequest
) -> JSONResponse:
    """Chunks text data assets into sub-segments and populates the database target."""
    db_context = request.app.db

    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    # Instantiate operational data layers
    project_model = await ProjectModel.create_instance(db_client=db_context)
    project = await project_model.get_project_or_create_one(project_id=project_id)

    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )

    asset_model = await AssetModel.create_instance(db_client=db_context)

    # 1. Resolve Target Assets File Index Matrix
    project_files_ids = {}
    if process_request.file_id:
        asset_record = await asset_model.get_asset_record(
            asset_project_id=project.id,
            asset_name=process_request.file_id
        )

        if asset_record is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"signal": ResponseSignal.FILE_ID_ERROR.value}
            )

        project_files_ids = {asset_record.id: asset_record.asset_name}
    else:
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.id,
            asset_type=AssetTypeEnum.FILE.value,
        )
        project_files_ids = {record.id: record.asset_name for record in project_files}

    if len(project_files_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": ResponseSignal.NO_FILES_ERROR.value}
        )
    
    process_controller = ProcessController(project_id=project_id)
    chunk_model = await ChunkModel.create_instance(db_client=db_context)

    # 2. Handle Document Overwrites Proactively
    if do_reset:

        logger.info(f"Purging legacy vector collections for project context: [{project.id}]")
        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
        await request.app.vectordb_client.delete_collection(collection_name=collection_name)
        
        logger.info(f"Purging legacy structural chunks for project context: [{project.id}]")
        await chunk_model.delete_chunks_by_project_id(project_id=project.id)

    # 3. Text Processing & Batched Chunk Populating
    no_records = 0
    no_files = 0

    for asset_id, file_id in project_files_ids.items():
        file_content = process_controller.get_file_content(file_id=file_id)

        if file_content is None:
            logger.error(f"Failed to access text contents for file tracking identifier: {file_id}")
            continue

        file_chunks = process_controller.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size
        )

        if not file_chunks:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"signal": ResponseSignal.PROCESSING_FAILED.value}
            )

        file_chunks_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i + 1,
                chunk_project_id=project.id,
                chunk_asset_id=asset_id
            )
            for i, chunk in enumerate(file_chunks)
        ]

        # Triggers our high-throughput PyMongo Async bulk write operations
        no_records += await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_files += 1

    logger.info(f"Successfully processed {no_files} files into {no_records} atomic chunks.")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": no_files
        }
    )

