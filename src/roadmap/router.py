from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from .schemas import RoadmapCreateRequest, RoadmapResponse, ErrorResponse
from .service import RoadmapService
from src.auth.utils import get_current_user_from_token
from src.auth.dtos import UserDTO

router = APIRouter(prefix="/roadmap", tags=["roadmap"])

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
        generated_roadmap_id = RoadmapService.create_roadmap(
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