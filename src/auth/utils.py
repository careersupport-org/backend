from datetime import datetime, timedelta
from typing import Optional
import jwt
import os
from dotenv import load_dotenv
from .exceptions import TokenExpiredError, InvalidTokenError, TokenDecodeError

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

def verify_token(token: str):
    if not SECRET_KEY:
        raise TokenDecodeError()
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidTokenError:
        raise InvalidTokenError()
    except Exception as e:
        raise TokenDecodeError() 