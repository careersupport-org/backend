from fastapi import Request
from fastapi.responses import JSONResponse
from src.common.exceptions import UnauthorizedException, EntityNotFoundException, ForbiddenException, ModelInvocationException
from src.auth.exceptions import JWTException
from src.roadmap.exceptions import RoadmapCreatorMaxCountException

import logging

logger = logging.getLogger(__name__)

def roadmap_creator_max_count_exception_handler(request: Request, exc: RoadmapCreatorMaxCountException):
    return JSONResponse(status_code=400, content={"message": exc.message})

def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(status_code=401, content={"message": exc.message})

def jwt_exception_handler(request: Request, exc: JWTException):
    return JSONResponse(status_code=401, content={"message": exc.message})

def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(status_code=403, content={"message": exc.message})

def entity_not_found_exception_handler(request: Request, exc: EntityNotFoundException):
    return JSONResponse(status_code=404, content={"message": exc.message})

def model_invocation_exception_handler(request: Request, exc: ModelInvocationException):
    logger.error(f"ModelInvocationException: {exc} in {request.url}")
    return JSONResponse(status_code=500, content={"message": exc.message})

def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected Exception: {exc} in {request.url}")
    return JSONResponse(status_code=500, content={"message": str(exc)})

