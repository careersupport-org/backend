import pytest
from datetime import datetime, timedelta, UTC
import jwt
from src.auth.utils import create_access_token, verify_token, SECRET_KEY, ALGORITHM
from src.auth.exceptions import TokenExpiredError, InvalidTokenError, TokenDecodeError

@pytest.fixture
def test_data():
    return {
        "sub": "123",
        "kakao_id": "456",
        "nickname": "test_user"
    }

def test_create_access_token_success(test_data):
    """JWT 토큰이 성공적으로 생성되는지 검증"""

    # Given: 사용자 정보가 주어짐
    user_data = test_data
    
    # When: 토큰 생성
    token = create_access_token(user_data)
    
    # Then: 토큰이 문자열이고 데이터가 올바르게 인코딩되어야 함
    assert isinstance(token, str)
    
    # 토큰 디코딩하여 데이터 검증
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == user_data["sub"]
    assert decoded["kakao_id"] == user_data["kakao_id"]
    assert decoded["nickname"] == user_data["nickname"]
    assert "exp" in decoded

def test_create_access_token_with_expires_delta(test_data):
    """만료 시간이 있는 JWT 토큰이 정상적으로 생성되는지 검증"""
    # Given: 사용자 정보와 만료 시간이 주어짐
    user_data = test_data
    expires_delta = timedelta(minutes=30)
    
    # When: 만료 시간을 지정하여 토큰 생성
    token = create_access_token(user_data, expires_delta)
    
    # Then: 토큰의 만료 시간이 지정된 시간과 일치해야 함
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    exp_timestamp = decoded["exp"]
    current_timestamp = int(datetime.now(UTC).timestamp())
    expected_exp_timestamp = current_timestamp + int(expires_delta.total_seconds())
    assert abs(exp_timestamp - expected_exp_timestamp) < 1

def test_verify_token_success(test_data):
    """유효한 JWT 토큰이 정상적으로 검증되는지 확인"""
    # Given: 유효한 토큰이 주어짐
    token = create_access_token(test_data)
    
    # When: 토큰 검증
    result = verify_token(token)
    
    # Then: 페이로드가 올바르게 검증되어야 함
    assert result.id == test_data["sub"]
    assert result.nickname == test_data["nickname"]

def test_verify_token_expired():
    """만료된 JWT 토큰에 대해 적절한 예외가 발생하는지 확인"""
    # Given: 만료된 토큰이 주어짐
    test_data = {"sub": "123"}
    token = jwt.encode(
        {
            **test_data,
            "exp": datetime.now(UTC) - timedelta(minutes=1)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    # When & Then: 만료된 토큰 검증 시도 시 예외 발생
    with pytest.raises(TokenExpiredError):
        verify_token(token)

def test_verify_token_invalid():
    """잘못된 시크릿 키로 생성된 토큰에 대해 적절한 예외가 발생하는지 확인"""
    # Given: 잘못된 시크릿 키로 토큰 생성
    invalid_token = jwt.encode(
        {"sub": "123"},
        "wrong_secret_key",
        algorithm=ALGORITHM
    )
    
    # When & Then: 잘못된 토큰 검증 시도 시 예외 발생
    with pytest.raises(InvalidTokenError):
        verify_token(invalid_token)

def test_verify_token_malformed():
    """잘못된 형식의 토큰에 대해 적절한 예외가 발생하는지 확인"""
    # Given: 잘못된 형식의 토큰
    malformed_token = "not.a.valid.jwt.token"
    
    # When & Then: 잘못된 형식의 토큰 검증 시도 시 예외 발생
    with pytest.raises(InvalidTokenError):
        verify_token(malformed_token)

def test_create_access_token_with_empty_data():
    """빈 데이터로 JWT 토큰이 정상적으로 생성되는지 확인"""
    # Given: 빈 데이터가 주어짐
    empty_data = {}
    
    # When: 빈 데이터로 토큰 생성
    token = create_access_token(empty_data)
    
    # Then: 토큰에는 만료 시간만 포함되어야 함
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    assert "exp" in decoded
    assert len(decoded) == 1  # exp만 있어야 함
