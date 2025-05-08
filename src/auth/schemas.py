from pydantic import BaseModel, Field
from typing import Optional

class LoginResponse(BaseModel):
    """로그인 응답"""
    code: str = Field(
        default="200",
        description="응답 상태 코드"
    )
    access_token: str = Field(
        description="JWT 액세스 토큰"
    )
    token_type: str = Field(
        default="bearer",
        description="토큰 타입"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": "200",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }

class ErrorResponse(BaseModel):
    """에러 응답"""
    code: str = Field(
        description="에러 코드"
    )
    detail: str = Field(
        description="에러 상세 메시지"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": "400",
                "detail": "로그인 처리 중 오류가 발생했습니다."
            }
        }

class UserInfo(BaseModel):
    """사용자 정보"""
    id: str = Field(
        description="사용자 ID"
    )
    nickname: str = Field(
        description="사용자 닉네임"
    )
    profile_image: Optional[str] = Field(
        description="사용자 프로필 이미지 URL"
    )

class ProfileUpdateRequest(BaseModel):
    """프로필 업데이트 요청"""
    profile: str = Field(
        description="사용자 프로필",
        max_length=500
    )

    class Config:
        json_schema_extra = {
            "example": {
                "profile": "안녕하세요! 저는 개발자입니다."
            }
        }

