from fastapi import APIRouter, HTTPException, Request, Depends, Header
from fastapi.responses import RedirectResponse
import httpx
from typing import Optional
import os

from sqlalchemy.orm import Session
from database import get_db
from .service import UserService
from .exceptions import JWTException, TokenExpiredError, InvalidTokenError, UserNotFoundError
from .utils import create_access_token, verify_token
from .schemas import LoginResponse, ErrorResponse, UserInfoSchema, ProfileUpdateRequest
from .dtos import UserDTO



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
                "sub": user.uid,
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

async def get_current_user_from_token(
    authorization: str = Header(..., description="Bearer token"),
    db: Session = Depends(get_db)
) -> UserDTO:
    """JWT 토큰에서 현재 사용자 정보를 추출합니다.
    
    Args:
        authorization (str): Authorization 헤더의 Bearer 토큰
        db (Session): 데이터베이스 세션
        
    Returns:
        UserDTO: 현재 인증된 사용자 정보
        
    Raises:
        HTTPException: 토큰이 없거나 유효하지 않은 경우
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                code="401",
                detail="인증 토큰이 필요합니다"
            ).dict()
        )
    
    token = authorization.split(" ")[1]
    try:
        return verify_token(token)
    except TokenExpiredError:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                code="401",
                detail="만료된 토큰입니다"
            ).dict()
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                code="401",
                detail="유효하지 않은 토큰입니다"
            ).dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                code="401",
                detail=f"인증 오류: {str(e)}"
            ).dict()
        )

@router.get("/me", response_model=UserInfoSchema, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"}
})
async def get_current_user(
    current_user: UserDTO = Depends(get_current_user_from_token)
):
    """현재 인증된 사용자 정보 반환
    
    Args:
        current_user (UserDTO): 현재 인증된 사용자 정보
        
    Returns:
        UserInfo: 사용자 정보
        
    Raises:
        HTTPException: 인증되지 않은 경우
    """
    return UserInfoSchema(
        id=current_user.uid,
        nickname=current_user.nickname,
        profile_image=current_user.profile_image
    )

@router.put("/me/profile", response_model=UserInfoSchema, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"}
})
async def update_profile(
    profile_update: ProfileUpdateRequest,
    current_user: UserDTO = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """사용자 프로필을 업데이트합니다.
    
    Args:
        profile_update (ProfileUpdateRequest): 업데이트할 프로필 정보
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        UserInfo: 업데이트된 사용자 정보
        
    Raises:
        HTTPException: 인증되지 않은 경우 또는 사용자를 찾을 수 없는 경우
    """
    try:
        user = UserService.update_user_profile(db, current_user.uid, profile_update.profile)
        return UserInfoSchema(
            id=user.uid,
            nickname=user.nickname,
            profile_image=user.profile_image
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                code="401",
                detail="사용자를 찾을 수 없습니다"
            ).dict()
        )
