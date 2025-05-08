from sqlalchemy.orm import Session
from .models import Roadmap
from langchain_core.load import load
from auth.service import UserService

class RoadmapService:

    roadmap_create_chain = load("chains/roadmap_create_chain.py")
    @staticmethod
    def create_roadmap(db: Session, user_uid: str, target_job: str, instruct: str) -> str:
        """로드맵을 생성합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            user_uid (str): 사용자 UID
            target_job (str): 목표 직무
            instruct (str): 로드맵 생성 지시사항
            
        Returns:
            Roadmap: 생성된 로드맵 정보
        """
        
