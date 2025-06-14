from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from .exceptions import RoadmapCreatorMaxCountException
from .models import Roadmap, RoadmapStep as RoadmapStepModel, Tag, LearningResource
from .config import LLMConfig
from src.auth.service import UserService
from src.auth.models import KakaoUser
from datetime import datetime
from src.common.exceptions import ModelInvocationException, EntityNotFoundException, ForbiddenException
import nanoid
import logging
from .schemas import (
    RoadmapListItemSchema, RoadmapDetailSchema, RoadmapStepSchema,
     LearningResourceSchema, LearningResourceListSchema, BookmarkedStepListResponse,
    BookmarkedStep
)
from fastapi.responses import StreamingResponse
import json
import asyncio
from src.roadmap.models import RoadmapStep as RoadmapStepModel, Roadmap as RoadmapModel, roadmap_subroadmap

class RoadmapService:
    roadmap_create_chain = LLMConfig.get_roadmap_create_llm()
    recommend_resource_chain = LLMConfig.get_recommend_resource_llm()
    step_guide_chain = LLMConfig.get_step_guide_llm()
    roadmap_assistant_chain = LLMConfig.get_roadmap_assistant_llm()
    subroadmap_create_chain = LLMConfig.get_subroadmap_create_llm()
    
    logger = logging.getLogger(__name__)

    @classmethod
    async def recommend_learning_resources(cls, db: Session, step_uid: str) -> LearningResourceListSchema:
        """로드맵 단계에 대한 학습 리소스를 추천합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            step_uid (str): 로드맵 단계 UID
            
        Returns:
            List[LearningResourceSchema]: 추천된 학습 리소스 목록
            
        Raises:
            EntityNotFoundException: 로드맵 단계를 찾을 수 없는 경우
        """
        step = db \
            .query(RoadmapStepModel) \
            .filter(RoadmapStepModel.unique_id == step_uid) \
            .options(
                joinedload(RoadmapStepModel.tags)
            ).first()

        if not step:
            raise Exception("Roadmap step not found")

        # 기존 학습 리소스 확인
        existing_resources = db \
            .query(LearningResource) \
            .filter(LearningResource.step_id == step.id) \
            .all()

        if existing_resources:
            return LearningResourceListSchema(
                resources=[
                    LearningResourceSchema(id=resource.unique_id, url=resource.url) 
                    for resource in existing_resources
                ])
        
        # LLM을 통해 학습 리소스 추천
        try:
            result = await cls.recommend_resource_chain.ainvoke({
                "description": step.title,
                "tags": " ,".join([tag.name for tag in step.tags]),
                "language": "korean"
            })
        except Exception as e:
            raise ModelInvocationException("학습 리소스 생성 중 오류가 발생했습니다.", e)
        
        result_list = []
        
        for url in result["url"]:
            learning_resource = LearningResource(
                unique_id=nanoid.generate(size=10),
                step_id=step.id,
                url=url
            )
            db.add(learning_resource)
            result_list.append(LearningResourceSchema(id=learning_resource.unique_id, url=learning_resource.url))
        
        db.commit()

        return LearningResourceListSchema(resources=result_list)

    @classmethod
    def get_roadmap_by_uid(cls, db: Session, roadmap_uid: str) -> RoadmapDetailSchema:
        """로드맵 상세 정보를 조회합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            roadmap_uid (str): 로드맵 UID
            
        Returns:
            RoadmapDetail: 로드맵 상세 정보
            
        Raises:
            EntityNotFoundException: 로드맵을 찾을 수 없는 경우
            ForbiddenException: 로드맵을 조회할 권한이 없는 경우
        """

        
        roadmap = db.query(Roadmap).filter(Roadmap.unique_id == roadmap_uid).first()

        if not roadmap:
            raise EntityNotFoundException("로드맵을 찾을 수 없습니다.")


        steps = []
        for step in roadmap.steps:
            step_detail = RoadmapStepSchema(
                id=step.unique_id,
                step=step.step,
                title=step.title,
                description=step.description,
                tags=[tag.name for tag in step.tags],
                subRoadMapId=step.sub_roadmap_uid,
                isBookmarked=step.is_bookmarked
            )
            steps.append(step_detail)

        steps.sort(key=lambda x: x.step)
        return RoadmapDetailSchema(
            id=roadmap.unique_id,
            title=roadmap.title,
            steps=steps,
            createdAt=roadmap.created_at,
            updatedAt=roadmap.updated_at
        )

    @classmethod
    def get_user_roadmaps(cls, db: Session, user_uid: str) -> list[RoadmapListItemSchema]:
        """사용자의 로드맵 목록을 조회합니다. 서브 로드맵은 조회하지 않습니다.
        
        Args:
            db (Session): 데이터베이스 세션
            user_uid (str): 사용자 UID
            
        Returns:
            list[RoadmapListItem]: 로드맵 목록
        """
        user = UserService.get_user_by_uid(db, user_uid)


        roadmaps = db.query(Roadmap).filter(
            Roadmap.user_id == user.id,
            Roadmap.parent_step == None
        ).order_by(Roadmap.created_at.desc()).all()
        
        return [
            RoadmapListItemSchema(
                uid=roadmap.unique_id,
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
            str: 생성된 로드맵 UID

        Raises:
            RoadmapCreatorMaxCountException: 3개 이상의 로드맵 및 서브 로드맵을 생성할 수 없는 경우
        """
        if await cls._check_roadmap_creator(db, user_uid):
            raise RoadmapCreatorMaxCountException("3개 이상의 로드맵 및 서브 로드맵을 생성할 수 없습니다.")


        current_date = datetime.now().strftime("%Y-%m-%d")
        user = UserService.get_user_by_uid(db, user_uid)
        
        roadmap_result = await cls.roadmap_create_chain.ainvoke({
            "language" : "korean",
            "target_job" : target_job,
            "user_background" : user.profile,
            "user_instructions" : instruct,
            "current_date" : current_date,
        })

        # Roadmap 생성
        roadmap = Roadmap(
            unique_id=nanoid.generate(size=10),
            user_id=user.id,
            title=roadmap_result['title']
        )

        # RoadmapStep 생성
        for step_data in roadmap_result['steps']:
            step = RoadmapStepModel(
                unique_id=nanoid.generate(size=10),
                step=step_data['step'],
                title=step_data['title'],
                description=step_data['description']
            )
            roadmap.steps.append(step)

            tags = [Tag(unique_id=nanoid.generate(size=10), name=tag) for tag in step_data['tags']]
            step.tags = tags

        db.add(roadmap)
        db.commit()
        return roadmap.unique_id
    

    @classmethod
    def delete_roadmap(cls, db: Session, roadmap_uid: str, current_user_uid: str):
        """로드맵을 삭제합니다.
        """
        roadmap = db.query(Roadmap).filter(Roadmap.unique_id == roadmap_uid).first()
        user = UserService.get_user_by_uid(db, current_user_uid)
        if not roadmap:
            raise EntityNotFoundException("로드맵을 찾을 수 없습니다.")
        
        if roadmap.user_id != user.id:
            raise ForbiddenException("로드맵을 삭제할 권한이 없습니다.")

        # 서브로드맵 관계 조회
        subroadmap_uids = db.execute(
            select(roadmap_subroadmap.c.subroadmap_uid).where(
                roadmap_subroadmap.c.roadmap_uid == roadmap.unique_id
            )
        ).scalars().all()

        # 서브로드맵 삭제
        if subroadmap_uids:
            db.query(Roadmap).filter(Roadmap.unique_id.in_(subroadmap_uids)).delete(synchronize_session=False)

        # 서브로드맵 관계 삭제
        db.execute(
            roadmap_subroadmap.delete().where(
                (roadmap_subroadmap.c.roadmap_uid == roadmap.unique_id) |
                (roadmap_subroadmap.c.subroadmap_uid == roadmap.unique_id)
            )
        )

        # 로드맵 삭제
        db.delete(roadmap)
        db.commit()

    @classmethod
    async def get_step_guide(cls, db: Session, step_uid: str):
        """
        로드맵 단계의 가이드를 스트리밍으로 반환합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            step_uid (str): 로드맵 단계 UID
            
        Returns:
            토큰 생성 제네레이터
        """
        
        step = db.query(RoadmapStepModel).filter(RoadmapStepModel.unique_id == step_uid).options(
            joinedload(RoadmapStepModel.roadmap),
            joinedload(RoadmapStepModel.tags)
        ).first()
        
        if not step:
            raise Exception("Roadmap step not found")

        async def generate_guide_in_db():
            for chunk in step.guide:
                yield f"data: {json.dumps({'token': chunk})}\n\n"

        if step.guide:
            return generate_guide_in_db()

        # 토큰을 저장할 공유 객체
        collected_tokens = []
        
        # 스트리밍이 완료된 후 작업할 이벤트
        streaming_completed = asyncio.Event()
        
        # 백그라운드 태스크 시작
        save_task = asyncio.create_task(
            cls._wait_and_save_guide(streaming_completed, collected_tokens, step_uid)
        )
        
        async def generate():
            try:
                async for chunk in cls.step_guide_chain.astream({
                    "description": step.description,
                    "tags": ", ".join([tag.name for tag in step.tags]),
                    "language": "korean"
                }):
                    token = chunk.content
                    collected_tokens.append(token)
                    yield f"data: {json.dumps({'token': token})}\n\n"
                
                # 스트리밍 완료 이벤트 설정
                streaming_completed.set()
                
            except Exception as e:
                # 에러 발생 시에도 이벤트 설정하여 백그라운드 태스크가 종료되도록 함
                streaming_completed.set()
                cls.logger.error(f"Error in streaming: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        return generate()
        

    @classmethod
    def toggle_bookmark(cls, db: Session, step_uid: str, current_user_uid: str) -> bool:
        """로드맵 단계의 북마크 상태를 토글합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            step_uid (str): 로드맵 단계 UID
            current_user_uid (str): 현재 접근한 사용자의 UID
            
        Returns:
            bool: 토글 후 북마크 상태 (True/False)
            
        Raises:
            EntityNotFoundException: 로드맵 단계를 찾을 수 없는 경우
            ForbiddenException: 권한이 없는 경우
        """

        step = db.query(RoadmapStepModel).filter(RoadmapStepModel.unique_id == step_uid).first()
        
        if not step:
            raise EntityNotFoundException("로드맵 Step을 조회할 수 없습니다.")

        # 로드맵 생성자 확인
        roadmap_creator = UserService.get_user_by_uid(db, step.roadmap.user.unique_id)
        if roadmap_creator.unique_id != current_user_uid:
            raise ForbiddenException("북마크 상태를 변경할 권한이 없습니다.")


        # 북마크 상태 토글
        step.is_bookmarked = not step.is_bookmarked
        db.commit()
        return step.is_bookmarked

 

    @classmethod
    def get_bookmarked_steps(cls, db: Session, user_uid: str) -> BookmarkedStepListResponse:
        """사용자의 북마크된 Step 목록을 조회합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            user_uid (str): 사용자 UID
            
        Returns:
            BookmarkedStepListResponse: 북마크된 Step 목록
        """
        # 사용자의 로드맵에서 북마크된 Step 조회
        bookmarked_steps = db.query(RoadmapStepModel).join(
            RoadmapStepModel.roadmap
        ).join(
            RoadmapModel.user
        ).filter(
            RoadmapStepModel.is_bookmarked == True,
            KakaoUser.unique_id == user_uid
        ).all()

        # 응답 형식으로 변환
        steps = [
            BookmarkedStep(
                title=step.title,
                roadmap_uid=step.roadmap.unique_id,
                step_uid=step.unique_id
            )
            for step in bookmarked_steps
        ]

        # 북마크된 Step이 없는 경우에도 빈 리스트 반환
        return BookmarkedStepListResponse(steps=steps)

        
    @classmethod
    async def call_roadmap_assistant(cls, db: Session, roadmap_uid: str, user_input: str) -> StreamingResponse:
        """로드맵 어시스턴트를 호출합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            roadmap_uid (str): 로드맵 UID
            user_input (str): 사용자 입력
        Returns:
            로드맵 어시스턴트 응답 제네레이터
        """

        # Roadmap 객체를 Pydantic 모델로 변환
        roadmap_detail = cls.get_roadmap_by_uid(db, roadmap_uid)
        roadmap_json = roadmap_detail.model_dump_json()

        async def generate():
            try:
                async for chunk in cls.roadmap_assistant_chain.astream({
                    "language": "korean",
                    "roadmap_object": roadmap_json,
                    "user_input": user_input
                }):
                    yield f"data: {json.dumps({'token': chunk.content})}\n\n"
            except Exception as e:
                cls.logger.error(f"Error in call_roadmap_assistant: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return generate()



    @classmethod
    async def create_subroadmap(cls, db: Session, step_uid: str, current_user_uid: str) -> str:
        """서브 로드맵을 생성합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            step_uid (str): 로드맵 단계 UID
            
        Returns:
            str: 생성된 서브 로드맵 UID
        
        Raises:
            RoadmapCreatorMaxCountException: 3개 이상의 로드맵 및 서브 로드맵을 생성할 수 없는 경우
        """

        if await cls._check_roadmap_creator(db, current_user_uid):
            raise RoadmapCreatorMaxCountException("3개 이상의 로드맵 및 서브 로드맵을 생성할 수 없습니다.")

        step = db.query(RoadmapStepModel).filter(RoadmapStepModel.unique_id == step_uid).options(
            joinedload(RoadmapStepModel.roadmap)
        ).first()

        if not step:
            raise EntityNotFoundException("로드맵 Step을 조회할 수 없습니다.")
        
        roadmap = step.roadmap
        
        subroadmap_result = await cls.subroadmap_create_chain.ainvoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "language": "korean",
            "topic_description": step.description,
            "topic_tags": ", ".join([tag.name for tag in step.tags]),
            "target_job": roadmap.title,
        })
        
        subroadmap = Roadmap(
            unique_id=nanoid.generate(size=10),
            user_id=roadmap.user_id,
            title=subroadmap_result['title']
        )

        step.sub_roadmap_uid = subroadmap.unique_id

        db.add(step)
        db.add(subroadmap)

        for step_data in subroadmap_result['steps']:
            step = RoadmapStepModel(
                unique_id=nanoid.generate(size=10),
                step=step_data['step'],
                title=step_data['title'],
                description=step_data['description'],
                tags=[Tag(unique_id=nanoid.generate(size=10), name=tag) for tag in step_data['tags']]
            )
            subroadmap.steps.append(step)

        db.commit()
        
        db.execute(roadmap_subroadmap.insert().values(
            roadmap_uid=roadmap.unique_id,
            subroadmap_uid=subroadmap.unique_id
        ))
        return subroadmap.unique_id

    @classmethod
    async def add_learning_resource(cls, db: Session, step_uid: str, url: str) -> LearningResourceSchema:
        """학습 리소스를 추가합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            step_uid (str): 로드맵 단계 UID
            url (str): 학습 리소스 URL

        Returns:
            LearningResourceSchema: 추가된 학습 리소스 정보
        """
        step = db.query(RoadmapStepModel).filter(RoadmapStepModel.unique_id == step_uid).first()
        if not step:
            raise EntityNotFoundException("로드맵 Step을 조회할 수 없습니다.")

        resource = LearningResource(
            unique_id=nanoid.generate(size=10),
            step_id=step.id,
            url=url
        )
        
        db.add(resource)
        db.commit()
        return LearningResourceSchema(id=resource.unique_id, url=resource.url)
    
    @classmethod
    async def remove_learning_resource(cls, db: Session, resource_uid: str) -> None:
        """학습 리소스를 삭제합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            resource_uid (str): 학습 리소스 UID

        Raises:
            EntityNotFoundException: 학습 리소스를 조회할 수 없는 경우
        """
        resource = db.query(LearningResource).filter(LearningResource.unique_id == resource_uid).first()
        if not resource:
            raise EntityNotFoundException("학습 리소스를 조회할 수 없습니다.")

        db.delete(resource)
        db.commit()
    
    @classmethod
    async def _check_roadmap_creator(cls, db: Session, current_user_uid: str) -> bool:
        """로드맵 생성자가 서브로드맵을 포함해 3개의 로드맵 이상을 생성했는지 확인합니다."""
        user_id = UserService.get_user_by_uid(db=db, user_uid=current_user_uid).id
        result = db.query(Roadmap).filter(Roadmap.user_id == user_id).count() >= 3

        return result
    

    @classmethod
    async def _wait_and_save_guide(cls, completed_event, tokens, step_uid):
        """스트리밍이 완료될 때까지 기다린 후 가이드를 저장하는 백그라운드 태스크"""
        try:
            # 스트리밍 완료 대기
            await completed_event.wait()
            
            # 토큰 결합하여 전체 가이드 생성
            complete_guide = "".join(tokens)
            
            # 새 DB 세션 생성 (기존 세션은 이미 닫혔을 수 있음)
            from sqlalchemy.orm import sessionmaker
            from database import engine
            
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            db = SessionLocal()
            
            try:
                step = db.query(RoadmapStepModel).filter(RoadmapStepModel.unique_id == step_uid).first()
                if step:
                    step.guide = complete_guide
                    db.commit()
                    cls.logger.info(f"Guide for step {step_uid} saved to DB")
                else:
                    cls.logger.error(f"Failed to save guide: Step {step_uid} not found")
            finally:
                db.close()
        except Exception as e:
            cls.logger.error(f"Error in background save task: {str(e)}")
