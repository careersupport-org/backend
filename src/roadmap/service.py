from sqlalchemy.orm import Session
from .models import Roadmap, RoadmapStep as RoadmapStepModel, Tag
from .config import LLMConfig
from src.auth.service import UserService
from datetime import datetime
import nanoid
import logging
import sys
import traceback
from .schemas import RoadmapListItemSchema, RoadmapDetailSchema, RoadmapStepSchema as RoadmapStepSchema, LearningResourceResponse, LearningResourceSchema


class RoadmapService:
    roadmap_create_chain = LLMConfig.get_roadmap_create_llm()
    recommend_resource_chain = LLMConfig.get_recommend_resource_llm()
    logger = logging.getLogger(__name__)

    @classmethod
    async def recommend_learning_resources(cls, db: Session, step_uid: str) -> LearningResourceResponse:
        """로드맵 단계에 대한 학습 리소스를 추천합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            step_uid (str): 로드맵 단계 UID
            
        Returns:
            LearningResourceResponse: 추천된 학습 리소스 목록
            
        Raises:
            Exception: 로드맵 단계를 찾을 수 없는 경우
        """
        step = db.query(RoadmapStepModel).filter(RoadmapStepModel.uid == step_uid).first()
        if not step:
            raise Exception("Roadmap step not found")

        try:
            # LLM을 통해 학습 리소스 추천
            result = await cls.recommend_resource_chain.ainvoke({
                "description": step.title,
                "tags": " ,".join([tag.name for tag in step.tags]),
                "language": "korean"
            })

            # 결과를 LearningResourceResponse 형식으로 변환
            resources = [
                LearningResourceSchema(
                    url=resource["url"],
                    resource_type=resource["resource_type"]
                )
                for resource in result["learning_resources"]
            ]

            return LearningResourceResponse(resources=resources)
        except Exception as e:
            error_msg = f"Error in recommend_learning_resources: {str(e)}\n"
            error_msg += f"Error type: {type(e).__name__}\n"
            error_msg += f"Traceback:\n{traceback.format_exc()}"
            cls.logger.error(error_msg)
            raise e

    @classmethod
    def get_roadmap_by_uid(cls, db: Session, roadmap_uid: str) -> RoadmapDetailSchema:
        """로드맵 상세 정보를 조회합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            roadmap_uid (str): 로드맵 UID
            
        Returns:
            RoadmapDetail: 로드맵 상세 정보
            
        Raises:
            Exception: 로드맵을 찾을 수 없는 경우
        """
        roadmap = db.query(Roadmap).filter(Roadmap.uid == roadmap_uid).first()
        if not roadmap:
            raise Exception("Roadmap not found")

        steps = []
        for step in roadmap.steps:
            step_detail = RoadmapStepSchema(
                id=step.uid,
                step=step.step,
                title=step.title,
                description=step.description,
                tags=[tag.name for tag in step.tags],
                subRoadMapId=None,  # 현재는 null로 설정
                isBookmarked=step.is_bookmarked
            )
            steps.append(step_detail)

        return RoadmapDetailSchema(
            id=roadmap.uid,
            title=roadmap.title,
            steps=steps,
            createdAt=roadmap.created_at,
            updatedAt=roadmap.updated_at
        )

    @classmethod
    def get_user_roadmaps(cls, db: Session, user_uid: str) -> list[RoadmapListItemSchema]:
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
            RoadmapListItemSchema(
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
                step = RoadmapStepModel(
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
        