from datetime import datetime, timedelta, UTC
from typing import Optional
import jwt
import os
from .exceptions import TokenExpiredException, InvalidTokenException, TokenDecodingException
from .dtos import UserDTO



# 기본값 설정
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7일

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    if not SECRET_KEY:
        raise TokenDecodingException()
        
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except jwt.PyJWTError as e:
        raise TokenDecodingException()
    except Exception as e:
        raise TokenDecodingException()

def verify_token(token: str) -> UserDTO:
    """JWT 토큰을 검증하고 사용자 정보를 반환합니다.
    
    Args:
        token (str): 검증할 JWT 토큰
        
    Returns:
        UserDTO: 디코딩된 사용자 정보
        
    Raises:
        TokenExpiredError: 토큰이 만료된 경우
        InvalidTokenError: 토큰이 유효하지 않은 경우
        TokenDecodeError: 토큰 디코딩 중 오류가 발생한 경우
    """
    if not SECRET_KEY:
        raise TokenDecodingException()
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return UserDTO(
            uid=payload["sub"],
            nickname=payload["nickname"],
            profile_image=payload.get("profile_image")
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException()
    except jwt.InvalidTokenError:
        raise InvalidTokenException()
    except Exception as e:
        raise TokenDecodingException() 
    
