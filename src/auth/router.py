from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import RedirectResponse
import httpx
import os

from sqlalchemy.orm import Session
from database import get_db
from .service import UserService
from .exceptions import TokenExpiredException, InvalidTokenException, TokenDecodingException
from .utils import create_access_token, verify_token
from .schemas import LoginResponse, ErrorResponse, UserInfoSchema, ProfileUpdateRequest, UserProfileSchema
from .dtos import UserDTO
from src.common.exceptions import UnauthorizedException
from src.common.schemas import OkResponse
from .context import get_current_user as get_current_user_from_token

router = APIRouter(prefix="/oauth", tags=["oauth"])

# 카카오 OAuth2 설정
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
default_profile_image_url = os.getenv("DEFAULT_PROFILE_IMAGE_URL")

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
        user = UserService.create_or_update_user(
            db,
            user_data["id"],
            user_data["properties"]["nickname"],
            user_data["properties"]["profile_image"] or default_profile_image_url
        )
        
        # JWT 토큰 생성
        token_data = {
            "sub": user.uid,
            "profile_image": user.profile_image,
            "nickname": user.nickname
        }
        access_token = create_access_token(data=token_data)
        
        return LoginResponse(
            code="200",
            access_token=access_token,
            token_type="bearer",
            user_id=user.uid,
            nickname=user.nickname,
            profile_image=user.profile_image
        )


@router.get("/me", response_model=UserInfoSchema, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"}
})
async def get_current_user(
    current_user: UserDTO = Depends(get_current_user_from_token)
):
    """현재 인증된 사용자 정보 반환(토큰 추출)
    
    Args:
        current_user (UserDTO): 현재 인증된 사용자 정보
        
    Returns:
        UserInfo: 사용자 정보
        
    Raises:
        UnauthorizedException: 인증되지 않은 경우
    """
    return UserInfoSchema(
        id=current_user.uid,
        nickname=current_user.nickname,
        profile_image=current_user.profile_image
    )

@router.put("/me/profile", response_model=OkResponse, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"}
})
def update_profile(
    profile_update: ProfileUpdateRequest,
    current_user: UserDTO = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
)-> dict:
    """사용자 프로필을 업데이트합니다.
    
    Args:
        profile_update (ProfileUpdateRequest): 업데이트할 프로필 정보
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        str: ok
        
    Raises:
        UnauthorizedException: 인증되지 않은 경우
    """

    UserService.update_user_profile(db, current_user.uid, profile_update.profile)
    return OkResponse()


@router.get("/me/profile", response_model=UserProfileSchema, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    404: {"model": ErrorResponse, "description": "사용자를 찾을 수 없음"}
})
async def get_my_profile(
    current_user: UserDTO = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """현재 인증된 사용자의 프로필 정보를 반환합니다.
    
    Args:
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        UserInfoSchema: 사용자 프로필 정보
        
    Raises:
        UnauthorizedException: 인증되지 않은 경우
    """
    user = UserService.get_user_by_uid(db, current_user.uid)

    return UserProfileSchema(
        id=user.unique_id,
        nickname=user.nickname,
        profile_image=user.profile_image,
        bio=user.profile
    )
