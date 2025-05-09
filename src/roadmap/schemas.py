from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

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

class RoadmapListItem(BaseModel):
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
    roadmaps: List[RoadmapListItem] = Field(description="로드맵 목록")

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