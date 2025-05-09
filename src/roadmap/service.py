from sqlalchemy.orm import Session
from .models import Roadmap, RoadmapStep, Tag
from langchain_core.load import load
from src.auth.service import UserService
from datetime import datetime
import nanoid
import os
import json
secrets_map={
    "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],

}

class RoadmapService:
    roadmap_create_chain_str = json.load(open("chains/roadmap_create_chain.json", "r"))
    roadmap_create_chain = load(roadmap_create_chain_str, secrets_map=secrets_map)

    @classmethod
    def create_roadmap(cls, db: Session, user_uid: str, target_job: str, instruct: str) -> str:
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
        
        roadmap_result = cls.roadmap_create_chain.invoke({
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
        return roadmap

        