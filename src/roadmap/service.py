from sqlalchemy.orm import Session, joinedload
from .models import Roadmap, RoadmapStep as RoadmapStepModel, Tag, LearningResource
from .config import LLMConfig
from src.auth.service import UserService
from src.auth.models import KakaoUser
from datetime import datetime
import nanoid
import logging
import sys
import traceback
from .schemas import (
    RoadmapListItemSchema, RoadmapDetailSchema, RoadmapStepSchema,
     LearningResourceSchema, LearningResourceListSchema, BookmarkedStepListResponse,
    BookmarkedStep
)
from fastapi.responses import StreamingResponse
import json
import asyncio

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
            Exception: 로드맵 단계를 찾을 수 없는 경우
        """
        step = db.query(RoadmapStepModel).filter(RoadmapStepModel.uid == step_uid).first()
        if not step:
            raise Exception("Roadmap step not found")

        try:
            # 기존 학습 리소스 확인
            existing_resources = db.query(LearningResource).filter(
                LearningResource.step_id == step.id
            ).all()

            if existing_resources:
                return LearningResourceListSchema(
                    resources=[
                        LearningResourceSchema(id=resource.uid, url=resource.url) 
                        for resource in existing_resources
                    ])
            # LLM을 통해 학습 리소스 추천
            result = await cls.recommend_resource_chain.ainvoke({
                "description": step.title,
                "tags": " ,".join([tag.name for tag in step.tags]),
                "language": "korean"
            })

            result_list = []
            # 새로운 학습 리소스 저장
            for url in result["url"]:
                learning_resource = LearningResource(
                    uid=nanoid.generate(size=10),
                    step_id=step.id,
                    url=url
                )
                db.add(learning_resource)

                result_list.append(LearningResourceSchema(id=learning_resource.uid, url=learning_resource.url))
            db.commit()

            return LearningResourceListSchema(resources=result_list)
        
        except Exception as e:
            error_msg = f"Error in recommend_learning_resources: {str(e)}\n"
            error_msg += f"Error type: {type(e).__name__}\n"
            error_msg += f"Traceback:\n{traceback.format_exc()}"
            cls.logger.error(error_msg)
            db.rollback()
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
                subRoadMapId=step.sub_roadmap_uid,
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
        roadmaps = db.query(Roadmap).filter(
            Roadmap.user_id == user.id,
            Roadmap.is_subroadmap == False
        ).order_by(Roadmap.created_at.desc()).all()
        
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
            db.flush()  

            # RoadmapStep 생성
            for step_data in roadmap_result['steps']:
                step = RoadmapStepModel(
                    uid=nanoid.generate(size=10),
                    roadmap_id=roadmap.id,  # flush 후 roadmap.id 사용
                    step=step_data['step'],
                    title=step_data['title'],
                    description=step_data['description']
                )
                db.add(step)
                db.flush() 
                # 태그 처리
                for tag_name in step_data['tags']:
                    tag = Tag(
                        step_id = step.id,
                        uid=nanoid.generate(size=10),
                        name=tag_name
                    )
                    db.add(tag)
                    db.flush()
                    step.tags.append(tag)

            db.commit()
            return roadmap.uid
        except Exception as e:
            error_msg = f"Error in create_roadmap: {str(e)}\n"
            error_msg += f"Error type: {type(e).__name__}\n"
            error_msg += f"Traceback:\n{traceback.format_exc()}"
            cls.logger.error(error_msg)
            db.rollback()
            raise e

    @classmethod
    async def get_step_guide(cls, db: Session, step_uid: str) -> StreamingResponse:
        step = db.query(RoadmapStepModel).filter(RoadmapStepModel.uid == step_uid).options(
            joinedload(RoadmapStepModel.roadmap),
            joinedload(RoadmapStepModel.tags)
        ).first()
        
        if not step:
            raise Exception("Roadmap step not found")

        async def generate_guide_in_db():
            for chunk in step.guide:
                yield f"data: {json.dumps({'token': chunk})}\n\n"

        if step.guide:
            return StreamingResponse(
                generate_guide_in_db(),
                media_type="text/event-stream"
            )

        # 토큰을 저장할 공유 객체
        collected_tokens = []
        
        # 스트리밍이 완료된 후 작업할 이벤트
        streaming_completed = asyncio.Event()
        
        try:
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

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        except Exception as e:
            # 메인 함수에서 에러 발생 시 이벤트 설정
            streaming_completed.set()
            cls.logger.error(f"Error in get_step_guide: {str(e)}")
            raise e

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
                step = db.query(RoadmapStepModel).filter(RoadmapStepModel.uid == step_uid).first()
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
            Exception: 로드맵 단계를 찾을 수 없는 경우
            Exception: 권한이 없는 경우
        """
        # 로드맵 단계와 관련된 로드맵 정보를 함께 조회
        step = db.query(RoadmapStepModel).filter(RoadmapStepModel.uid == step_uid).options(
            joinedload(RoadmapStepModel.roadmap)
        ).first()
        
        if not step:
            raise Exception("Roadmap step not found")

        # 로드맵 생성자 확인
        roadmap_creator = UserService.find_user(db, step.roadmap.user.uid)
        if roadmap_creator.uid != current_user_uid:
            raise Exception("Permission denied")

        try:
            # 북마크 상태 토글
            step.is_bookmarked = not step.is_bookmarked
            db.commit()
            return step.is_bookmarked
        except Exception as e:
            db.rollback()
            error_msg = f"Error in toggle_bookmark: {str(e)}\n"
            error_msg += f"Error type: {type(e).__name__}\n"
            error_msg += f"Traceback:\n{traceback.format_exc()}"
            cls.logger.error(error_msg)
            raise e

    @classmethod
    def get_bookmarked_steps(cls, db: Session, user_uid: str) -> BookmarkedStepListResponse:
        """사용자의 북마크된 Step 목록을 조회합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            user_uid (str): 사용자 UID
            
        Returns:
            BookmarkedStepListResponse: 북마크된 Step 목록
        """
        try:
            # 사용자의 로드맵에서 북마크된 Step 조회
            bookmarked_steps = db.query(RoadmapStepModel).join(
                RoadmapStepModel.roadmap
            ).join(
                KakaoUser,
                Roadmap.user_id == KakaoUser.id
            ).filter(
                RoadmapStepModel.is_bookmarked == True,
                KakaoUser.uid == user_uid
            ).all()

            # 응답 형식으로 변환
            steps = [
                BookmarkedStep(
                    title=step.title,
                    roadmap_uid=step.roadmap.uid,
                    step_uid=step.uid
                )
                for step in bookmarked_steps
            ]

            # 북마크된 Step이 없는 경우에도 빈 리스트 반환
            return BookmarkedStepListResponse(steps=steps)
        except Exception as e:
            error_msg = f"Error in get_bookmarked_steps: {str(e)}\n"
            error_msg += f"Error type: {type(e).__name__}\n"
            error_msg += f"Traceback:\n{traceback.format_exc()}"
            cls.logger.error(error_msg)
            # 북마크된 Step이 없는 경우에도 빈 리스트 반환
            return BookmarkedStepListResponse(steps=[])
        
    @classmethod
    async def call_roadmap_assistant(cls, db: Session, roadmap_uid: str, user_input: str) -> StreamingResponse:
        """로드맵 어시스턴트를 호출합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            roadmap_uid (str): 로드맵 UID
            user_input (str): 사용자 입력
        Returns:
            StreamingResponse: 로드맵 어시스턴트 응답
        """

        roadmap = db.query(Roadmap).filter(Roadmap.uid == roadmap_uid).first()
        if not roadmap:
            raise Exception("Roadmap not found")

        try:
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

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        except Exception as e:
            cls.logger.error(f"Error in call_roadmap_assistant: {str(e)}")
            raise e


    @classmethod
    async def create_subroadmap(cls, db: Session, step_uid: str) -> str:
        """서브 로드맵을 생성합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            step_uid (str): 로드맵 단계 UID
            
        Returns:
            str: 생성된 서브 로드맵 UID
        """
        step = db.query(RoadmapStepModel).filter(RoadmapStepModel.uid == step_uid).options(
            joinedload(RoadmapStepModel.roadmap)
        ).first()

        if not step:
            raise Exception("Roadmap step not found")
        
        roadmap = step.roadmap
        
        subroadmap_result = await cls.subroadmap_create_chain.ainvoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "language": "korean",
            "topic_description": step.description,
            "topic_tags": ", ".join([tag.name for tag in step.tags]),
            "target_job": roadmap.title,
        })
        
        subroadmap = Roadmap(
            uid=nanoid.generate(size=10),
            user_id=roadmap.user_id,
            is_subroadmap=True,
            title=subroadmap_result['title']
        )
        db.add(subroadmap)
        db.commit()

        for step_data in subroadmap_result['steps']:
            step = RoadmapStepModel(
                uid=nanoid.generate(size=10),
                roadmap_id=subroadmap.id,
                step=step_data['step'],
                title=step_data['title'],
                description=step_data['description'],
                tags=[Tag(uid=nanoid.generate(size=10), name=tag) for tag in step_data['tags']]
            )
            db.add(step)

        db.query(RoadmapStepModel).filter(RoadmapStepModel.uid == step_uid).update(
            {"sub_roadmap_uid": subroadmap.uid}
        )
        cls.logger.info(f"Subroadmap created and linked: {subroadmap.uid}")
        db.commit()

        return subroadmap.uid
