from datetime import datetime, timedelta
from typing import Optional
import jwt
import os
from dotenv import load_dotenv
from .exceptions import TokenExpiredError, InvalidTokenError, TokenDecodeError
from .dtos import UserDTO

load_dotenv(".env")

# 기본값 설정
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7일

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    if not SECRET_KEY:
        raise TokenDecodeError()
        
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except jwt.PyJWTError as e:
        raise TokenDecodeError()
    except Exception as e:
        raise TokenDecodeError()

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
        raise TokenDecodeError()
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return UserDTO(
            id=payload["sub"],
            nickname=payload["nickname"],
            profile_image=payload.get("profile_image")
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidTokenError:
        raise InvalidTokenError()
    except Exception as e:
        raise TokenDecodeError() 
    
