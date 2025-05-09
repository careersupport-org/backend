from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from src.roadmap.models import Roadmap

class KakaoUser(Base):
    __tablename__ = "kakao_users"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(10), unique=True, index=True, nullable=False)
    kakao_id = Column(BigInteger, unique=True, index=True, nullable=False)
    nickname = Column(String(100), nullable=False)
    profile_image = Column(String(500), nullable=True)
    profile = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_logined_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    roadmaps = relationship(Roadmap, back_populates="user")

    def __repr__(self):
        return f"<KakaoUser(id={self.id}, kakao_id={self.kakao_id}, nickname={self.nickname})>"
