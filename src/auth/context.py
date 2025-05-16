from fastapi import Header, Depends
from src.auth.utils import verify_token
from src.auth.dtos import UserDTO
from src.common.exceptions import UnauthorizedException
from database import get_db
from sqlalchemy.orm import Session


async def get_current_user(
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
        raise UnauthorizedException("Token not found")
    
    token = authorization.split(" ")[1]

    return verify_token(token)