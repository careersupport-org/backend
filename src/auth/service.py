from sqlalchemy.orm import Session
from src.auth.models import KakaoUser
from datetime import datetime

class KakaoUserService:
    @staticmethod
    def get_user_by_kakao_id(db: Session, kakao_id: int):
        return db.query(KakaoUser).filter(KakaoUser.kakao_id == kakao_id).first()

    @staticmethod
    def create_or_update_user(db: Session, user_info: dict):
        kakao_id = user_info["id"]
        nickname = user_info["properties"]["nickname"]
        profile_image = user_info["properties"]["profile_image"]

        user = KakaoUserService.get_user_by_kakao_id(db, kakao_id)
        
        if user:
            # 기존 사용자 정보 업데이트
            user.nickname = nickname
            user.profile_image = profile_image
            user.last_logined_at = datetime.utcnow()
        else:
            # 새 사용자 생성
            user = KakaoUser(
                kakao_id=kakao_id,
                nickname=nickname,
                profile_image=profile_image
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        return user 