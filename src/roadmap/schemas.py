from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Literal

class RoadmapCreateRequest(BaseModel):
    """로드맵 생성 요청"""
    target_job: str = Field(
        description="목표 직무",
        min_length=1,
        max_length=100
    )
    instruct: str = Field(
        description="로드맵 생성 지시사항",
        min_length=1,
        max_length=1000
    )

    class Config:
        json_schema_extra = {
            "example": {
                "target_job": "백엔드 개발자",
                "instruct": "Java와 Spring을 사용하는 백엔드 개발자가 되기 위한 로드맵을 생성해주세요."
            }
        }

class RoadmapResponse(BaseModel):
    """로드맵 응답"""
    id: str = Field(description="로드맵 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "testroadmap123",
            }
        }

class RoadmapListItemSchema(BaseModel):
    """로드맵 목록 아이템"""
    uid: str = Field(description="로드맵 UID")
    title: str = Field(description="로드맵 제목")
    created_at: datetime = Field(description="생성일")
    updated_at: datetime = Field(description="수정일")

    class Config:
        json_schema_extra = {
            "example": {
                "uid": "testroadmap123",
                "title": "Java 백엔드 개발자 로드맵",
                "created_at": "2024-03-20T10:00:00",
                "updated_at": "2024-03-20T10:00:00"
            }
        }

class RoadmapListResponse(BaseModel):
    """로드맵 목록 응답"""
    roadmaps: List[RoadmapListItemSchema] = Field(description="로드맵 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "roadmaps": [
                    {
                        "uid": "testroadmap123",
                        "title": "Java 백엔드 개발자 로드맵",
                        "created_at": "2024-03-20T10:00:00",
                        "updated_at": "2024-03-20T10:00:00"
                    }
                ]
            }
        }

class RoadmapStepSchema(BaseModel):
    """로드맵 단계 상세 정보"""
    id: str = Field(description="단계 ID")
    step: int = Field(description="단계 번호")
    title: str = Field(description="단계 제목")
    description: str = Field(description="단계 설명")
    tags: List[str] = Field(description="태그 목록")
    subRoadMapId: Optional[str] = Field(None, description="하위 로드맵 ID")
    isBookmarked: bool = Field(False, description="북마크 여부")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "step123",
                "step": 1,
                "title": "Java 기본기 강화",
                "description": "Java 기본기 강화에 대한 상세설명..",
                "tags": ["Java", "Basic"],
                "subRoadMapId": None,
                "isBookmarked": False
            }
        }

class RoadmapDetailSchema(BaseModel):
    """로드맵 상세 정보"""
    id: str = Field(description="로드맵 ID")
    title: str = Field(description="로드맵 제목")
    steps: List[RoadmapStepSchema] = Field(description="로드맵 단계 목록")
    createdAt: datetime = Field(description="생성일")
    updatedAt: datetime = Field(description="수정일")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "roadmap123",
                "title": "Java 백엔드 개발자 로드맵",
                "steps": [
                    {
                        "id": "step123",
                        "step": 1,
                        "title": "Java 기본기 강화",
                        "description": "Java 기본기 강화에 대한 상세설명..",
                        "tags": ["Java", "Basic"],
                        "subRoadMapId": None,
                        "isBookmarked": False
                    }
                ],
                "createdAt": "2024-03-20T10:00:00",
                "updatedAt": "2024-03-20T10:00:00"
            }
        }

class LearningResourceSchema(BaseModel):
    """학습 리소스"""
    id: str = Field(description="리소스 ID")
    url: str = Field(description="리소스 URL")


    class Config:
        json_schema_extra = {
            "example": {
                "id": "resource123",
                "url": "https://docs.oracle.com/javase/tutorial/"
            }
        }

class LearningResourceListSchema(BaseModel):
    """학습 리소스 목록"""
    resources: List[LearningResourceSchema] = Field(description="학습 리소스 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "resources": [
                    {
                        "id": "resource123",
                        "url": "https://docs.oracle.com/javase/tutorial/"
                    }
                ]
            }
        }

class LearningResourceCreateResponse(BaseModel):
    url: str = Field(..., description="학습 리소스 URL")


class ErrorResponse(BaseModel):
    """에러 응답"""
    code: str = Field(description="에러 코드")
    detail: str = Field(description="에러 상세 메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "400",
                "detail": "잘못된 요청입니다."
            }
        }

class BookmarkedStep(BaseModel):
    """북마크된 Step 정보"""
    title: str = Field(description="단계 제목")
    roadmap_uid: str = Field(description="로드맵 UID")
    step_uid: str = Field(description="Step UID")

    class Config:
        json_schema_extra = {
            "example": {
                "roadmap_uid": "roadmap123",
                "step_uid": "step123"
            }
        }

class BookmarkedStepListResponse(BaseModel):
    """북마크된 Step 목록 응답"""
    steps: List[BookmarkedStep] = Field(description="북마크된 Step 목록")

    class Config:
        json_schema_extra = {
            "example": {
                "steps": [
                    {
                        "roadmap_uid": "roadmap123",
                        "step_uid": "step123"
                    }
                ]
            }
        }