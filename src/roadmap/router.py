from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from .schemas import (
    RoadmapCreateRequest, RoadmapResponse, RoadmapListResponse,
    RoadmapDetailSchema, LearningResourceListSchema, ErrorResponse,
    BookmarkedStepListResponse, LearningResourceCreateResponse,
    LearningResourceCreateResponse, LearningResourceSchema
)
from .service import RoadmapService
from src.auth.context import get_current_user
from src.auth.dtos import UserDTO
from fastapi.responses import StreamingResponse
import logging
from src.auth.models import KakaoUser
from .schemas import RoadmapAssistantUserInputSchema

router = APIRouter(prefix="/roadmap", tags=["roadmap"])
logger = logging.getLogger(__name__)


@router.get("/bookmarks", response_model=BookmarkedStepListResponse, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def get_bookmarked_steps(
    current_user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> BookmarkedStepListResponse:
    """사용자의 북마크된 Step 목록을 조회합니다.
    
    Args:
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        BookmarkedStepListResponse: 북마크된 Step 목록
    """
    return RoadmapService.get_bookmarked_steps(db, current_user.uid)


@router.get("", response_model=RoadmapListResponse, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def get_roadmaps(
    current_user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자의 로드맵 목록을 조회합니다.
    
    Args:
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        RoadmapListResponse: 로드맵 목록
    """
    roadmaps = RoadmapService.get_user_roadmaps(db, current_user.uid)
    return RoadmapListResponse(roadmaps=roadmaps)



@router.get("/{roadmap_uid}", response_model=RoadmapDetailSchema, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    404: {"model": ErrorResponse, "description": "로드맵을 찾을 수 없음"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def get_roadmap(
    roadmap_uid: str,
    current_user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """로드맵 상세 정보를 조회합니다.
    
    Args:
        roadmap_uid (str): 로드맵 UID
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        RoadmapDetail: 로드맵 상세 정보
    """
    roadmap = RoadmapService.get_roadmap_by_uid(db, roadmap_uid)
    return roadmap


@router.get("/step/{step_uid}/resources", response_model=LearningResourceListSchema, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    404: {"model": ErrorResponse, "description": "로드맵 단계를 찾을 수 없음"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def get_learning_resources(
    step_uid: str,
    current_user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """로드맵 단계에 대한 학습 리소스를 추천합니다.
    
    Args:
        step_uid (str): 로드맵 단계 UID
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        LearningResourceSchema: 추천된 학습 리소스 목록
    """
    resources = await RoadmapService.recommend_learning_resources(db, step_uid)
    return resources


@router.get("/step/{step_uid}/guide", responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    404: {"model": ErrorResponse, "description": "로드맵 단계를 찾을 수 없음"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def get_step_guide(
    step_uid: str,
    current_user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """로드맵 단계에 대한 상세 가이드를 스트리밍합니다.
    
    Args:
        step_uid (str): 로드맵 단계 UID
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        StreamingResponse: SSE 스트리밍 응답
    """
    token_generator = await RoadmapService.get_step_guide(db, step_uid)
    return StreamingResponse(token_generator, media_type="text/event-stream")


@router.post("", response_model=RoadmapResponse, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    400: {"model": ErrorResponse, "description": "잘못된 요청"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def create_roadmap(
    roadmap_request: RoadmapCreateRequest,
    current_user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """로드맵을 생성합니다.
    
    Args:
        roadmap_request (RoadmapCreateRequest): 로드맵 생성 요청 정보
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        RoadmapResponse: 생성된 로드맵 정보
    """
    # 로드맵 생성
    generated_roadmap_id = await RoadmapService.create_roadmap(
        db=db,
        user_uid=current_user.uid,
        target_job=roadmap_request.target_job,
        instruct=roadmap_request.instruct
    )
    
    return RoadmapResponse(
        id=generated_roadmap_id
    )

@router.post("/step/{step_uid}/bookmark", responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    403: {"model": ErrorResponse, "description": "권한 없음"},
    404: {"model": ErrorResponse, "description": "로드맵 단계를 찾을 수 없음"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def toggle_bookmark(
    step_uid: str,
    current_user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """로드맵 단계의 북마크 상태를 토글합니다.
    
    Args:
        step_uid (str): 로드맵 단계 UID
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        dict: 토글 후 북마크 상태
    """
    is_bookmarked = RoadmapService.toggle_bookmark(db, step_uid, current_user.uid)
    return {"is_bookmarked": is_bookmarked}


@router.post("/{roadmap_uid}/assistant", responses={
    200: {"description": "로드맵 어시스턴트 응답"},
    401: {"description": "인증 오류"},
    404: {"description": "로드맵을 찾을 수 없음"},
    500: {"description": "서버 오류"}
})
async def call_roadmap_assistant(
    roadmap_uid: str,
    request: RoadmapAssistantUserInputSchema,
    db: Session = Depends(get_db)
):
    """로드맵 어시스턴트를 호출합니다.
    
    Args:
        roadmap_uid (str): 로드맵 UID
        request (UserInputRequest): 사용자 입력
        db (Session): 데이터베이스 세션
        
    Returns:
        StreamingResponse: 로드맵 어시스턴트 응답
    """
    assistant_generator = await RoadmapService.call_roadmap_assistant(
        db=db,
        roadmap_uid=roadmap_uid,
        user_input=request.user_input
    )
    return StreamingResponse(assistant_generator, media_type="text/event-stream")


@router.post("/step/{step_uid}/subroadmap", responses={
    200: {"description": "서브 로드맵 생성 성공"},
    401: {"model": ErrorResponse, "description": "인증 오류"},
    404: {"model": ErrorResponse, "description": "로드맵 단계를 찾을 수 없음"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def create_subroadmap(
    step_uid: str,
    current_user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> RoadmapResponse:
    """로드맵 단계에 대한 서브 로드맵을 생성합니다.
    
    Args:
        step_uid (str): 로드맵 단계 UID
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        RoadmapResponse: 생성된 서브 로드맵 UID
    """
    subroadmap_uid = await RoadmapService.create_subroadmap(db, step_uid, current_user.uid)
    return RoadmapResponse(id=subroadmap_uid)


@router.post("/step/{step_id}/resources", response_model=LearningResourceSchema)
async def add_learning_resource(
    step_id: str,
    resource: LearningResourceCreateResponse,
    db: Session = Depends(get_db),
    current_user: KakaoUser = Depends(get_current_user)
):
    """
    로드맵 단계에 학습 리소스를 추가합니다.
    """
    return await RoadmapService.add_learning_resource(db, step_id, resource.url)

@router.delete("/step/resources/{resource_uid}", responses={
    200: {"description": "학습 리소스 삭제 성공"},
    401: {"model": ErrorResponse, "description": "인증 오류"},
    404: {"model": ErrorResponse, "description": "학습 리소스를 찾을 수 없음"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def remove_learning_resource(
    resource_uid: str,
    current_user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """학습 리소스를 삭제합니다.
    
    Args:
        resource_uid (str): 학습 리소스 UID
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
    """
    await RoadmapService.remove_learning_resource(db, resource_uid)
    return "ok"
