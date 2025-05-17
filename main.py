from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.auth.router import router as auth_router
from src.roadmap.router import router as roadmap_router
from database import Base, engine, init_db
from src.auth.models import KakaoUser
from src.common.exceptions import UnauthorizedException, EntityNotFoundException, ForbiddenException
from src.auth.exceptions import JWTException
from src.roadmap.exceptions import RoadmapCreatorMaxCountException
from src.common.exception_router import (
    roadmap_creator_max_count_exception_handler,
    unauthorized_exception_handler,
    jwt_exception_handler,
    forbidden_exception_handler,
    entity_not_found_exception_handler,
    general_exception_handler
)
from dotenv import load_dotenv
import logging
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
app = FastAPI()

# CORS 설정
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 예외 핸들러 등록
app.add_exception_handler(RoadmapCreatorMaxCountException, roadmap_creator_max_count_exception_handler)
app.add_exception_handler(UnauthorizedException, unauthorized_exception_handler)
app.add_exception_handler(JWTException, jwt_exception_handler)
app.add_exception_handler(ForbiddenException, forbidden_exception_handler)
app.add_exception_handler(EntityNotFoundException, entity_not_found_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

if os.getenv("RUNNING_ENVIRONMENT") == "development":
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialization completed")

app.include_router(auth_router)
app.include_router(roadmap_router)

logger.info(f"Server is running on {os.getenv('RUNNING_ENVIRONMENT')} environment")