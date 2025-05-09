from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from .schemas import RoadmapCreateRequest, RoadmapResponse, RoadmapListResponse, RoadmapDetail, ErrorResponse
from .service import RoadmapService
from src.auth.router import get_current_user_from_token
from src.auth.dtos import UserDTO

router = APIRouter(prefix="/roadmap", tags=["roadmap"])

@router.get("/{roadmap_uid}", response_model=RoadmapDetail, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    404: {"model": ErrorResponse, "description": "로드맵을 찾을 수 없음"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def get_roadmap(
    roadmap_uid: str,
    current_user: UserDTO = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """로드맵 상세 정보를 조회합니다.
    
    Args:
        roadmap_uid (str): 로드맵 UID
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        RoadmapDetail: 로드맵 상세 정보
        
    Raises:
        HTTPException: 인증되지 않은 경우, 로드맵을 찾을 수 없는 경우 또는 서버 오류 발생 시
    """
    try:
        roadmap = RoadmapService.get_roadmap_by_uid(db, roadmap_uid)
        return roadmap
    except Exception as e:
        if str(e) == "Roadmap not found":
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    code="404",
                    detail="로드맵을 찾을 수 없습니다."
                ).dict()
            )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                code="500",
                detail=f"서버 오류: {str(e)}"
            ).dict()
        )

@router.get("", response_model=RoadmapListResponse, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def get_roadmaps(
    current_user: UserDTO = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """사용자의 로드맵 목록을 조회합니다.
    
    Args:
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        RoadmapListResponse: 로드맵 목록
        
    Raises:
        HTTPException: 인증되지 않은 경우 또는 서버 오류 발생 시
    """
    try:
        roadmaps = RoadmapService.get_user_roadmaps(db, current_user.uid)
        return RoadmapListResponse(roadmaps=roadmaps)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                code="500",
                detail=f"서버 오류: {str(e)}"
            ).dict()
        )

@router.post("", response_model=RoadmapResponse, responses={
    401: {"model": ErrorResponse, "description": "인증 오류"},
    400: {"model": ErrorResponse, "description": "잘못된 요청"},
    500: {"model": ErrorResponse, "description": "서버 오류"}
})
async def create_roadmap(
    roadmap_request: RoadmapCreateRequest,
    current_user: UserDTO = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """로드맵을 생성합니다.
    
    Args:
        roadmap_request (RoadmapCreateRequest): 로드맵 생성 요청 정보
        current_user (UserDTO): 현재 인증된 사용자 정보
        db (Session): 데이터베이스 세션
        
    Returns:
        RoadmapResponse: 생성된 로드맵 정보
        
    Raises:
        HTTPException: 인증되지 않은 경우 또는 서버 오류 발생 시
    """
    try:
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
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                code="500",
                detail=f"서버 오류: {str(e)}"
            ).dict()
        ) 