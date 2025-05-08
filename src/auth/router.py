from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
import httpx
from typing import Optional
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
from .service import UserService
from .exceptions import JWTException
from .utils import create_access_token
from .schemas import LoginResponse, ErrorResponse

load_dotenv(".env")

router = APIRouter(prefix="/oauth", tags=["oauth"])

# 카카오 OAuth2 설정
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")

@router.get("/kakao/login")
async def kakao_login():
    """카카오 로그인 페이지로 리다이렉트"""
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?client_id={KAKAO_CLIENT_ID}&redirect_uri={KAKAO_REDIRECT_URI}&response_type=code"
    return RedirectResponse(kakao_auth_url)

@router.get("/kakao/callback", response_model=LoginResponse, responses={
    400: {"model": ErrorResponse, "description": "로그인 처리 중 오류 발생"},
    401: {"model": ErrorResponse, "description": "인증 오류"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def kakao_callback(code: str, db: Session = Depends(get_db)):
    """카카오 로그인 콜백 처리"""
    try:
        # 액세스 토큰 받기
        token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": KAKAO_CLIENT_ID,
            "client_secret": KAKAO_CLIENT_SECRET,
            "redirect_uri": KAKAO_REDIRECT_URI,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=data)
            token_response.raise_for_status()
            token_data = token_response.json()
            
            # 사용자 정보 가져오기
            user_info_url = "https://kapi.kakao.com/v2/user/me"
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            user_response = await client.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # 사용자 정보 저장 또는 업데이트
            user = UserService.create_or_update_user(db, user_data)
            
            # JWT 토큰 생성
            token_data = {
                "sub": str(user.id),
                "kakao_id": str(user.kakao_id),
                "nickname": user.nickname
            }
            access_token = create_access_token(data=token_data)
            
            return LoginResponse(
                code="200",
                access_token=access_token,
                token_type="bearer"
            )
            
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                code="400",
                detail=f"로그인 처리 중 오류 발생: {str(e)}"
            ).dict()
        )
    except JWTException as e:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                code="401",
                detail=e.message
            ).dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                code="500",
                detail=f"서버 오류: {str(e)}"
            ).dict()
        )
