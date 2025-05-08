from pydantic import BaseModel
from typing import Optional

class UserDTO(BaseModel):
    """JWT 토큰에서 디코딩된 사용자 정보를 담는 DTO"""
    id: str
    nickname: str
    profile_image: Optional[str] = None
