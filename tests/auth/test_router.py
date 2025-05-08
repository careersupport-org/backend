import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.auth.models import KakaoUser
from main import app
import httpx

client = TestClient(app)


@pytest.fixture
def mock_user():
    """테스트용 사용자 객체를 반환합니다."""
    return KakaoUser(
        id=1,
        kakao_id=123456789,
        nickname="테스트유저",
        profile_image="https://example.com/profile.jpg",
        last_logined_at=datetime.utcnow()
    )

@pytest.fixture
def mock_kakao_user_info():
    """테스트용 카카오 사용자 정보를 반환합니다."""
    return {
        "id": 123456789,
        "properties": {
            "nickname": "테스트유저",
            "profile_image": "https://example.com/profile.jpg"
        }
    }


@patch("httpx.AsyncClient.post")
@patch("httpx.AsyncClient.get")
@patch("src.auth.service.UserService.create_or_update_user")
def test_kakao_callback_success(
    mock_create_user,
    mock_get_user_info,
    mock_get_token,
    mock_user,
    mock_kakao_user_info
):
    """시나리오: 카카오 로그인 콜백 성공
    
    Given: 유효한 인증 코드가 주어졌을 때
    When: /oauth/kakao/callback 엔드포인트에 GET 요청을 보내면
    Then: JWT 토큰이 포함된 로그인 응답이 반환되어야 함
    """
    # Given: 모의 응답 설정
    mock_get_token.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=lambda: {"access_token": "mock_access_token"}
    )
    mock_get_user_info.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=lambda: mock_kakao_user_info
    )
    mock_create_user.return_value = mock_user
    
    # When: 카카오 콜백 요청
    response = client.get("/oauth/kakao/callback?code=test_code")
    
    # Then: 성공 응답 확인
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "200"
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # API 호출 검증
    mock_get_token.assert_called_once()
    mock_get_user_info.assert_called_once()
    mock_create_user.assert_called_once()

@patch("httpx.Response.raise_for_status")
def test_kakao_callback_invalid_code(mock_get_token):
    """시나리오: 잘못된 인증 코드로 카카오 로그인 시도
    
    Given: 잘못된 인증 코드가 주어졌을 때
    When: /oauth/kakao/callback 엔드포인트에 GET 요청을 보내면
    Then: 400 에러 응답이 반환되어야 함
    """
    # Given: 모의 에러 응답 설정
    mock_get_token.side_effect = httpx.HTTPError(
        "400 Bad Request"
    )

    # When: 잘못된 코드로 카카오 콜백 요청
    response = client.get("/oauth/kakao/callback?code=invalid_code")
    
    # Then: 에러 응답 확인
    assert response.status_code == 400
    data = response.json()

    assert data["detail"]["code"] == "400"
    assert "로그인 처리 중 오류 발생" in data["detail"]["detail"]

@patch("httpx.AsyncClient.post")
@patch("httpx.AsyncClient.get")
@patch("src.auth.service.UserService.create_or_update_user")
def test_kakao_callback_server_error(
    mock_create_user,
    mock_get_user_info,
    mock_get_token,
    mock_kakao_user_info
):
    """시나리오: 서버 오류 발생
    
    Given: 서버에서 예기치 않은 오류가 발생했을 때
    When: /oauth/kakao/callback 엔드포인트에 GET 요청을 보내면
    Then: 500 에러 응답이 반환되어야 함
    """
    # Given: 모의 응답 설정
    mock_get_token.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=lambda: {"access_token": "mock_access_token"}
    )
    mock_get_user_info.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=lambda: mock_kakao_user_info
    )
    mock_create_user.side_effect = Exception("Database error")
    
    # When: 카카오 콜백 요청
    response = client.get("/oauth/kakao/callback?code=test_code")
    
    # Then: 에러 응답 확인
    assert response.status_code == 500
    data = response.json()
    assert data["detail"]["code"] == "500"
    assert "서버 오류" in data["detail"]["detail"] 