from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.auth.router import router as auth_router
from src.roadmap.router import router as roadmap_router
from database import Base, engine
from src.auth.models import KakaoUser
from dotenv import load_dotenv
import logging
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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

# 데이터베이스 초기화
if os.getenv("CREATE_DATABASE", "false") == "true":
    Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(roadmap_router)
