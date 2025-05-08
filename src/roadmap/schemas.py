from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

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