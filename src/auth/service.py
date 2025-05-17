from sqlalchemy.orm import Session
from src.auth.models import KakaoUser
from datetime import datetime, UTC
import nanoid
from src.common.exceptions import EntityNotFoundException, UnauthorizedException
from typing import Optional
import os
from sqlalchemy import select
from src.auth.dtos import UserDTO
default_profile_image_url = os.getenv("DEFAULT_PROFILE_IMAGE_URL")

class UserService:
    @staticmethod
    def get_user_by_uid(db: Session, user_uid: str) -> KakaoUser:
        """사용자 프로필을 조회합니다.
        
        Args:
            db (Session): 데이터베이스 세션
            user_uid (str): 사용자 UID
            
        Returns:
            KakaoUser: 사용자 프로필 정보
            
        Raises:
            UnauthorizedException: 사용자를 찾을 수 없는 경우
        """
        stmt = (
            select(KakaoUser)
            .where(KakaoUser.unique_id == user_uid)
        )

        user = db.execute(stmt).one_or_none()
        if not user:
            raise UnauthorizedException("User not found")
        return user 


    @staticmethod
    def get_user_by_kakao_id(db: Session, kakao_id: int) -> KakaoUser:
        """
        사용자를 kakao_id로 조회합니다.
        사용자가 존재하지 않으면 EntityNotFoundException을 발생시킵니다.

        Args:
            db (Session): 데이터베이스 세션
            kakao_id (int): 카카오 아이디

        Returns:
            KakaoUser: 사용자 정보
        """
        stmt = (
            select(KakaoUser)
            .where(KakaoUser.kakao_id == kakao_id)
        )

        user = db.execute(stmt).one_or_none()
        if not user:
            raise EntityNotFoundException(f"User with kakao_id {kakao_id} not found")
        return user
    
    @staticmethod
    def create_or_update_user(db: Session, kakao_id: int, nickname: str, profile_image: Optional[str] = None) -> UserDTO:
        """
        사용자 정보를 생성하거나 업데이트합니다.
        사용자가 존재하지 않으면 생성하고, 존재하면 업데이트합니다.

        Args:
            db (Session): 데이터베이스 세션
            kakao_id (int): 카카오 아이디
            nickname (str): 닉네임
            profile_image (str): 프로필 이미지

        Returns:
            UserDTO: 사용자 정보
        """


        user = db.query(KakaoUser).filter(KakaoUser.kakao_id == kakao_id).first()

        if user:
            # 기존 사용자 정보 업데이트
            user.nickname = nickname
            user.profile_image = profile_image or default_profile_image_url
            user.last_logined_at = datetime.now(UTC)
        else:
            # 새 사용자 생성
            user = KakaoUser(
                kakao_id=kakao_id,
                unique_id=nanoid.generate(size=10),
                nickname=nickname,
                profile_image=profile_image or default_profile_image_url
            )
            db.add(user)
        
        db.commit()
        return UserDTO(
            uid=user.unique_id,
            nickname=user.nickname,
            profile_image=user.profile_image
        )

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
            UnauthorizedException: 사용자를 찾을 수 없는 경우
        """


        user = db.query(KakaoUser).filter(KakaoUser.unique_id == user_uid).first()
        if not user:
            raise UnauthorizedException("User not found")
            
        user.profile = profile
        db.commit()
        return "ok"
