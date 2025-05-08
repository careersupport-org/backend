import pytest
from datetime import datetime, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.auth.service import UserService
from src.auth.models import Base, KakaoUser
import nanoid
from src.auth.exceptions import UserNotFoundError

# 테스트용 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./sqp_test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """테스트용 데이터베이스 세션을 생성하고 테스트 후 정리합니다."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    yield db


@pytest.fixture
def sample_user_info():
    """테스트용 카카오 사용자 정보를 반환합니다."""
    return {
        "id": 123456789,
        "properties": {
            "nickname": "테스트유저",
            "profile_image": "https://example.com/profile.jpg"
        }
    }

def test_get_user_by_kakao_id_existing_user(db_session, sample_user_info):
    """시나리오: 존재하는 카카오 ID로 사용자 조회
    
    Given: 데이터베이스에 저장된 사용자가 있을 때
    When: 해당 사용자의 카카오 ID로 get_user_by_kakao_id를 호출하면
    Then: 해당 사용자 객체가 반환되어야 함
    """
    # Given: 데이터베이스에 사용자 생성
    user = KakaoUser(
        uid=nanoid.generate(size=10),
        kakao_id=sample_user_info["id"],
        nickname=sample_user_info["properties"]["nickname"],
        profile_image=sample_user_info["properties"]["profile_image"]
    )
    db_session.add(user)
    db_session.commit()
    
    # When: 카카오 ID로 사용자 조회
    found_user = UserService.get_user_by_kakao_id(db_session, sample_user_info["id"])
    
    # Then: 사용자 정보가 일치해야 함
    assert found_user is not None
    assert found_user.kakao_id == sample_user_info["id"]
    assert found_user.nickname == sample_user_info["properties"]["nickname"]
    assert found_user.profile_image == sample_user_info["properties"]["profile_image"]

    db_session.query(KakaoUser).delete()
    db_session.commit()

def test_get_user_by_kakao_id_nonexistent_user(db_session):
    """시나리오: 존재하지 않는 카카오 ID로 사용자 조회
    
    Given: 데이터베이스에 저장된 사용자가 없을 때
    When: 존재하지 않는 카카오 ID로 get_user_by_kakao_id를 호출하면
    Then: None이 반환되어야 함
    """
    # Given: 데이터베이스가 비어있음
    
    # When: 존재하지 않는 카카오 ID로 사용자 조회
    found_user = UserService.get_user_by_kakao_id(db_session, 999999999)
    
    # Then: None이 반환되어야 함
    assert found_user is None
    db_session.query(KakaoUser).delete()
    db_session.commit()

def test_create_or_update_user_new_user(db_session, sample_user_info):
    """시나리오: 새로운 사용자 생성
    
    Given: 데이터베이스에 저장된 사용자가 없을 때
    When: 새로운 사용자 정보로 create_or_update_user를 호출하면
    Then: 새로운 사용자가 생성되어야 함
    """
    # Given: 데이터베이스가 비어있음
    
    # When: 새로운 사용자 생성
    created_user = UserService.create_or_update_user(db_session, sample_user_info)
    
    # Then: 사용자가 정상적으로 생성되어야 함
    assert created_user is not None
    assert created_user.kakao_id == sample_user_info["id"]
    assert created_user.nickname == sample_user_info["properties"]["nickname"]
    assert created_user.profile_image == sample_user_info["properties"]["profile_image"]
    assert created_user.last_logined_at is not None
    db_session.query(KakaoUser).delete()
    db_session.commit()

def test_create_or_update_user_existing_user(db_session, sample_user_info):
    """시나리오: 기존 사용자 정보 업데이트
    
    Given: 데이터베이스에 저장된 사용자가 있을 때
    When: 해당 사용자의 새로운 정보로 create_or_update_user를 호출하면
    Then: 사용자 정보가 업데이트되어야 함
    """
    # Given: 기존 사용자 생성
    original_user = KakaoUser(
        uid=nanoid.generate(size=10),
        kakao_id=sample_user_info["id"],
        nickname="이전닉네임",
        profile_image="https://example.com/old_profile.jpg"
    )
    db_session.add(original_user)
    db_session.commit()
    
    # When: 사용자 정보 업데이트
    updated_user = UserService.create_or_update_user(db_session, sample_user_info)
    
    # Then: 사용자 정보가 업데이트되어야 함
    assert updated_user is not None
    assert updated_user.kakao_id == sample_user_info["id"]
    assert updated_user.nickname == sample_user_info["properties"]["nickname"]
    assert updated_user.profile_image == sample_user_info["properties"]["profile_image"]
    assert updated_user.last_logined_at is not None
    db_session.query(KakaoUser).delete()
    db_session.commit()
    

def test_create_or_update_user_invalid_info(db_session):
    """시나리오: 잘못된 사용자 정보로 사용자 생성/업데이트 시도
    
    Given: 필수 정보가 누락된 사용자 정보가 있을 때
    When: create_or_update_user를 호출하면
    Then: KeyError 예외가 발생해야 함
    """
    # Given: 필수 정보가 누락된 사용자 정보
    invalid_user_info = {
        "id": 123456789,
        "properties": {
            "nickname": "테스트유저"
            # profile_image 누락
        }
    }
    
    # When & Then: KeyError 예외 발생 확인
    with pytest.raises(KeyError):
        UserService.create_or_update_user(db_session, invalid_user_info)

    db_session.query(KakaoUser).delete()
    db_session.commit()

def test_update_user_profile_success(db_session):
    """시나리오: 사용자 프로필 업데이트 성공
    
    Given: 데이터베이스에 사용자가 존재할 때
    When: update_user_profile 메서드를 호출하면
    Then: 사용자의 프로필이 업데이트되어야 함
    """
    # Given: 테스트용 사용자 생성
    user = KakaoUser(
        kakao_id=123456789,
        uid="test123",
        nickname="테스트유저",
        profile_image="https://example.com/profile.jpg",
        last_logined_at=datetime.now(UTC)
    )
    db_session.add(user)
    db_session.commit()
    
    # When: 프로필 업데이트
    updated_user = UserService.update_user_profile(
        db=db_session,
        user_uid="test123",
        profile="안녕하세요! 저는 개발자입니다."
    )
    
    # Then: 프로필이 업데이트되었는지 확인
    assert updated_user.profile == "안녕하세요! 저는 개발자입니다."
    assert updated_user.uid == "test123"
    assert updated_user.nickname == "테스트유저"
    assert updated_user.profile_image == "https://example.com/profile.jpg"

    db_session.query(KakaoUser).delete()
    db_session.commit()

def test_update_user_profile_not_found(db_session):
    """시나리오: 존재하지 않는 사용자의 프로필 업데이트 시도
    
    Given: 데이터베이스에 사용자가 존재하지 않을 때
    When: update_user_profile 메서드를 호출하면
    Then: UserNotFoundError가 발생해야 함
    """
    # Given: 데이터베이스가 비어있는 상태
    
    # When & Then: 존재하지 않는 사용자의 프로필 업데이트 시도
    with pytest.raises(UserNotFoundError):
        UserService.update_user_profile(
            db=db_session,
            user_uid="nonexistent",
            profile="새로운 프로필"
        )
    db_session.query(KakaoUser).delete()
    db_session.commit()

def test_update_user_profile_empty(db_session):
    """시나리오: 빈 프로필로 업데이트
    
    Given: 데이터베이스에 사용자가 존재할 때
    When: 빈 문자열로 프로필을 업데이트하면
    Then: 프로필이 빈 문자열로 업데이트되어야 함
    """
    # Given: 테스트용 사용자 생성
    user = KakaoUser(
        kakao_id=123456789,
        uid="test123",
        nickname="테스트유저",
        profile_image="https://example.com/profile.jpg",
        last_logined_at=datetime.now(UTC)
    )
    db_session.add(user)
    db_session.commit()
    
    # When: 빈 프로필로 업데이트
    updated_user = UserService.update_user_profile(
        db=db_session,
        user_uid="test123",
        profile=""
    )
    
    # Then: 프로필이 빈 문자열로 업데이트되었는지 확인
    assert updated_user.profile == ""
    assert updated_user.uid == "test123"
    assert updated_user.nickname == "테스트유저"
    assert updated_user.profile_image == "https://example.com/profile.jpg"
    db_session.query(KakaoUser).delete()
    db_session.commit()

def test_find_user_success(db_session):
    """사용자 조회 성공 테스트"""
    # Given
    user = KakaoUser(
        kakao_id=123456789,
        uid="test_uid_1",
        nickname="Test User",
        profile_image="https://example.com/profile.jpg",
        profile="Test profile",
        last_logined_at=datetime.now(UTC)
    )
    db_session.add(user)
    db_session.commit()

    # When
    found_user = UserService.find_user(db_session, "test_uid_1")

    # Then
    assert found_user is not None
    assert found_user.uid == "test_uid_1"
    assert found_user.nickname == "Test User"
    assert found_user.profile_image == "https://example.com/profile.jpg"
    assert found_user.profile == "Test profile"

    db_session.query(KakaoUser).delete()
    db_session.commit()

def test_find_user_profile_not_found(db_session):
    """존재하지 않는 사용자 조회 테스트"""
    # Given
    non_existent_uid = "non_existent_uid"

    # When & Then
    with pytest.raises(UserNotFoundError) as exc_info:
        UserService.find_user(db_session, non_existent_uid)
    
def test_find_user_profile_empty_db(db_session):
    """빈 데이터베이스에서 사용자 프로필 조회 테스트"""
    # Given
    test_uid = "test_uid_2"

    # When & Then
    with pytest.raises(UserNotFoundError) as exc_info:
        UserService.find_user(db_session, test_uid)
    db_session.query(KakaoUser).delete()
    db_session.commit()