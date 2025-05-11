from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import nanoid

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
    steps = relationship("RoadmapStep", back_populates="roadmap", cascade="all, delete-orphan", foreign_keys="RoadmapStep.roadmap_id")
    parent_step = relationship("RoadmapStep", back_populates="sub_roadmap", foreign_keys="RoadmapStep.sub_roadmap_uid")
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
    sub_roadmap_uid = Column(String(10), ForeignKey('roadmaps.uid'), nullable=True)
    
    # 관계 설정
    roadmap = relationship("Roadmap", back_populates="steps", foreign_keys=[roadmap_id])
    sub_roadmap = relationship("Roadmap", back_populates="parent_step", foreign_keys=[sub_roadmap_uid])
    tags = relationship("Tag", back_populates="step", cascade="all, delete-orphan")
    learning_resources = relationship("LearningResource", back_populates="step")

    def __repr__(self):
        return f"<RoadmapStep(id={self.id}, step={self.step}, title={self.title})>"

class Tag(Base):
    """태그 모델"""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=False)
    step_id = Column(Integer, ForeignKey('roadmap_steps.id'), nullable=False)
    
    # 관계 설정
    step = relationship("RoadmapStep", back_populates="tags", foreign_keys=[step_id])

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"

class LearningResource(Base):
    """학습 리소스 모델"""
    __tablename__ = "learning_resources"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String(10), unique=True, index=True, nullable=False)
    step_id = Column(Integer, ForeignKey('roadmap_steps.id'), nullable=False)
    url = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계 설정
    step = relationship("RoadmapStep", back_populates="learning_resources")

    def __repr__(self):
        return f"<LearningResource(id={self.id}, url={self.url}, resource_type={self.resource_type})>" 