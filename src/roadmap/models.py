from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import nanoid

# RoadmapStep과 Tag의 다대다 관계를 위한 중간 테이블
roadmap_step_tags = Table(
    'roadmap_step_tags',
    Base.metadata,
    Column('roadmap_step_id', Integer, ForeignKey('roadmap_steps.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Roadmap(Base):
    """로드맵 모델"""
    __tablename__ = "roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(10), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('kakao_users.id'), nullable=False)
    title = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 관계 설정
    steps = relationship("RoadmapStep", back_populates="roadmap", cascade="all, delete-orphan")
    user = relationship("KakaoUser", back_populates="roadmaps")

    def __repr__(self):
        return f"<Roadmap(id={self.id}, title={self.title})>"

class RoadmapStep(Base):
    """로드맵 단계 모델"""
    __tablename__ = "roadmap_steps"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(10), unique=True, index=True, nullable=False)
    roadmap_id = Column(Integer, ForeignKey('roadmaps.id'), nullable=False)
    step = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=False)
    guide = Column(String(2048), nullable=True)
    is_bookmarked = Column(Boolean, default=False, nullable=False)

    # 관계 설정
    roadmap = relationship("Roadmap", back_populates="steps")
    tags = relationship("Tag", secondary=roadmap_step_tags, back_populates="steps")

    def __repr__(self):
        return f"<RoadmapStep(id={self.id}, step={self.step}, title={self.title})>"

class Tag(Base):
    """태그 모델"""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(50), unique=False, nullable=False)

    # 관계 설정
    steps = relationship("RoadmapStep", secondary=roadmap_step_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>" 