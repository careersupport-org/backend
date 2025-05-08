from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.auth.router import router as auth_router
from database import Base, engine
from src.auth.models import KakaoUser

app = FastAPI()

# CORS 설정
origins = [
    "http://localhost:3000",  # React 개발 서버
    "http://localhost:8000",  # FastAPI 개발 서버
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 초기화
Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
