from fastapi import Request
from fastapi.responses import JSONResponse
from src.common.exceptions import UnauthorizedException, EntityNotFoundException
from src.auth.exceptions import JWTException
from main import app



@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(status_code=401, content={"message": exc.message})

@app.exception_handler(JWTException)
async def jwt_exception_handler(request: Request, exc: JWTException):
    return JSONResponse(status_code=401, content={"message": exc.message})

@app.exception_handler(EntityNotFoundException)
async def entity_not_found_exception_handler(request: Request, exc: EntityNotFoundException):
    return JSONResponse(status_code=404, content={"message": exc.message})

