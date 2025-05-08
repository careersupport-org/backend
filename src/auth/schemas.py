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
    """카카오 사용자 정보"""
    id: int = Field(
        description="카카오 사용자 ID"
    )
    properties: dict = Field(
        description="카카오 사용자 프로필 정보",
        example={
            "nickname": "홍길동",
            "profile_image": "https://example.com/profile.jpg"
        }
    ) 