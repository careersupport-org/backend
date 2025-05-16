from fastapi import Request
from fastapi.responses import JSONResponse
from src.common.exceptions import UnauthorizedException, EntityNotFoundException, ForbiddenException
from src.auth.exceptions import JWTException
from src.roadmap.exceptions import RoadmapCreatorMaxCountException
from main import app


import logging

logger = logging.getLogger(__name__)



@app.exception_handler(RoadmapCreatorMaxCountException)
async def roadmap_creator_max_count_exception_handler(request: Request, exc: RoadmapCreatorMaxCountException):
    return JSONResponse(status_code=400, content={"message": exc.message})

@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(status_code=401, content={"message": exc.message})

@app.exception_handler(JWTException)
async def jwt_exception_handler(request: Request, exc: JWTException):
    return JSONResponse(status_code=401, content={"message": exc.message})

@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(status_code=403, content={"message": exc.message})

@app.exception_handler(EntityNotFoundException)
async def entity_not_found_exception_handler(request: Request, exc: EntityNotFoundException):
    return JSONResponse(status_code=404, content={"message": exc.message})

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected Exception: {exc} in {request.url}")
    return JSONResponse(status_code=500, content={"message": str(exc)})

