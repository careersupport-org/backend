import pytest
from datetime import datetime, UTC
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.roadmap.service import RoadmapService
from src.roadmap.models import Base, Roadmap, RoadmapStep, Tag
from src.auth.models import KakaoUser
import nanoid
from unittest.mock import patch, MagicMock

# 테스트용 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./roadmap_test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """테스트용 데이터베이스 세션을 생성하고 테스트 후 정리합니다."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_user(db_session):
    """테스트용 사용자를 생성합니다."""
    user = KakaoUser(
        unique_id=nanoid.generate(size=10),
        kakao_id=123456789,
        nickname="테스트유저",
        profile_image="https://example.com/profile.jpg",
        profile="테스트 프로필입니다."
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def mock_chain():
    """LangChain chain을 mocking합니다."""
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {
        'title': 'Java Backend Engineer Roadmap',
        'description': 'A structured learning roadmap for Java Backend Engineer',
        'steps': [
            {
                'step': 1,
                'title': 'Java 기본기 강화',
                'description': 'Java의 기본 문법, 데이터 타입, 연산자, 제어문, 함수 등에 대해 복습하고, Java 8의 새로운 기능들에 대해 학습합니다.',
                'tags': ['Java', 'Basic']
            },
            {
                'step': 2,
                'title': 'Spring Framework 깊이 이해하기',
                'description': 'Spring Framework의 핵심 개념인 IoC, AOP, Bean Life Cycle 등에 대해 깊이 이해하고, Spring MVC, Spring WebFlux 등에 대해 학습합니다.',
                'tags': ['Spring', 'Framework']
            }
        ]
    }
    return mock_chain

def test_create_roadmap_success(db_session, sample_user, mock_chain):
    """시나리오: 로드맵 생성 성공
    
    Given: 유효한 사용자 정보와 로드맵 생성 요청이 있을 때
    When: create_roadmap을 호출하면
    Then: 로드맵과 단계들이 정상적으로 생성되어야 함
    """
    # Given
    target_job = "Java Backend Engineer"
    instruct = "Java 백엔드 개발자가 되기 위한 로드맵을 만들어주세요."

    # When
    with patch('langchain_core.load', return_value=mock_chain):
        roadmap = RoadmapService.create_roadmap(
            db=db_session,
            user_uid=sample_user.uid,
            target_job=target_job,
            instruct=instruct
        )

    # Then
    assert roadmap is not None
    assert roadmap.title == 'Java Backend Engineer Roadmap'
    assert roadmap.uid is not None
    assert roadmap.user_id == sample_user.id

    # 단계들이 정상적으로 생성되었는지 확인
    steps = db_session.query(RoadmapStep).filter(RoadmapStep.roadmap_id == roadmap.id).all()
    assert len(steps) == 2  # mock_chain에서 반환한 steps의 길이와 일치

    # 각 단계의 태그가 정상적으로 생성되었는지 확인
    for step in steps:
        assert step.uid is not None
        assert step.title is not None
        assert step.description is not None
        assert len(step.tags) > 0

def test_create_roadmap_with_invalid_user(db_session, mock_chain):
    """시나리오: 존재하지 않는 사용자로 로드맵 생성 시도
    
    Given: 존재하지 않는 사용자 UID가 있을 때
    When: create_roadmap을 호출하면
    Then: UserNotFoundError가 발생해야 함
    """
    # Given
    invalid_user_uid = "invalid_uid"
    target_job = "Java Backend Engineer"
    instruct = "Java 백엔드 개발자가 되기 위한 로드맵을 만들어주세요."

    # When & Then
    with patch('langchain_core.load', return_value=mock_chain):
        with pytest.raises(Exception):  # UserNotFoundError
            RoadmapService.create_roadmap(
                db=db_session,
                user_uid=invalid_user_uid,
                target_job=target_job,
                instruct=instruct
            )

 