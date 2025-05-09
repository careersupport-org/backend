from sqlalchemy.orm import Session
from .models import Roadmap, RoadmapStep, Tag
from .config import LLMConfig
from src.auth.service import UserService
from datetime import datetime
import nanoid
import logging
import sys
import traceback
from .schemas import RoadmapListItem


class RoadmapService:
    roadmap_create_chain = LLMConfig.get_roadmap_create_llm()
    logger = logging.getLogger(__name__)

    @classmethod
    def get_user_roadmaps(cls, db: Session, user_uid: str) -> list[RoadmapListItem]:
        """사용자의 로드맵 목록을 조회합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            user_uid (str): 사용자 UID
            
        Returns:
            list[RoadmapListItem]: 로드맵 목록
        """
        user = UserService.find_user(db, user_uid)
        roadmaps = db.query(Roadmap).filter(Roadmap.user_id == user.id).order_by(Roadmap.created_at.desc()).all()
        
        return [
            RoadmapListItem(
                uid=roadmap.uid,
                title=roadmap.title,
                created_at=roadmap.created_at,
                updated_at=roadmap.updated_at
            )
            for roadmap in roadmaps
        ]

    @classmethod
    async def create_roadmap(cls, db: Session, user_uid: str, target_job: str, instruct: str) -> str:
        """로드맵을 생성합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            user_uid (str): 사용자 UID
            target_job (str): 목표 직무
            instruct (str): 로드맵 생성 지시사항
            
        Returns:
            Roadmap: 생성된 로드맵 정보
        """
        print(f"create_roadmap 호출")
        current_date = datetime.now().strftime("%Y-%m-%d")
        user = UserService.find_user(db, user_uid)
        try:
            roadmap_result = await cls.roadmap_create_chain.ainvoke({
                    "language" : "korean",
                    "target_job" : target_job,
                "user_background" : user.profile,
                "user_instructions" : instruct,
                "current_date" : current_date,
            })

            # Roadmap 생성
            roadmap = Roadmap(
                uid=nanoid.generate(size=10),
                user_id=user.id,
                title=roadmap_result['title']
            )
            db.add(roadmap)
            db.flush()  # roadmap.id를 얻기 위해 flush

            # RoadmapStep 생성
            for step_data in roadmap_result['steps']:
                step = RoadmapStep(
                    uid=nanoid.generate(size=10),
                    roadmap_id=roadmap.id,
                    step=step_data['step'],
                    title=step_data['title'],
                    description=step_data['description']
                )
                
                # 태그 처리
                for tag_name in step_data['tags']:
                    tag = Tag(
                        uid=nanoid.generate(size=10),
                        name=tag_name
                    )
                    db.add(tag)
                    db.flush()
                    step.tags.append(tag)
                
                db.add(step)

            db.commit()
            return roadmap.uid
        except Exception as e:
            error_msg = f"Error in create_roadmap: {str(e)}\n"
            error_msg += f"Error type: {type(e).__name__}\n"
            error_msg += f"Traceback:\n{traceback.format_exc()}"
            cls.logger.error(error_msg)
            db.rollback()
            raise e
        