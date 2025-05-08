from sqlalchemy.orm import Session
from src.auth.models import KakaoUser
from datetime import datetime, UTC
import nanoid
from .exceptions import UserNotFoundError

class UserService:
    @staticmethod
    def get_user_by_kakao_id(db: Session, kakao_id: int):
        return db.query(KakaoUser).filter(KakaoUser.kakao_id == kakao_id).first()

    @staticmethod
    def create_or_update_user(db: Session, user_info: dict):
        kakao_id = user_info["id"]
        nickname = user_info["properties"]["nickname"]
        profile_image = user_info["properties"]["profile_image"]

        user = UserService.get_user_by_kakao_id(db, kakao_id)
        
        if user:
            # 기존 사용자 정보 업데이트
            user.nickname = nickname
            user.profile_image = profile_image
            user.last_logined_at = datetime.now(UTC)
        else:
            # 새 사용자 생성
            user = KakaoUser(
                kakao_id=kakao_id,
                uid=nanoid.generate(size=10),
                nickname=nickname,
                profile_image=profile_image
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user_profile(db: Session, user_uid: str, profile: str) -> KakaoUser:
        """사용자 프로필을 업데이트합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            user_uid (str): 사용자 UID
            profile (str): 업데이트할 프로필 내용
            
        Returns:
            KakaoUser: 업데이트된 사용자 정보
            
        Raises:
            UserNotFoundError: 사용자를 찾을 수 없는 경우
        """
        user = db.query(KakaoUser).filter(KakaoUser.uid == user_uid).first()
        if not user:
            raise UserNotFoundError()
            
        user.profile = profile
        db.commit()
        db.refresh(user)
        return user 