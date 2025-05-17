from pydantic import BaseModel, Field

class OkResponse(BaseModel):
    message: str = Field(
        description="메시지", default="ok"
    )

    class Config:
        json_schema_extra = {
            "example": {"message": "ok"}
        }
