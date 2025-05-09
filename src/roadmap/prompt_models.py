from typing import List, Literal
from datetime import datetime
from pydantic import BaseModel, Field

class RoadMapStep(BaseModel):
    """
    Road map step information including details and metadata.
    
    Attributes:
        step: The numerical order of this step in the roadmap
        title: The title or name of this step
        description: Detailed explanation of what this step involves
        tags: List of relevant keywords or categories for this step
    """
    step: int = Field(description="The numerical order of this step in the roadmap")
    title: str = Field(description="The title or name of this step")
    description: str = Field(description="Detailed explanation of what this step involves")
    tags: List[str] = Field(description="List of relevant keywords or categories for this step")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RoadMap(BaseModel):
    """
    A structured learning or development roadmap with ordered steps.
    
    Attributes:
        title: The main title of the roadmap
        description: Overview explanation of the roadmap's purpose and content
        steps: Ordered list of steps that make up the roadmap
    """
    title: str = Field(description="The main title of the roadmap")
    description: str = Field(description="Overview explanation of the roadmap's purpose and content")
    steps: List[RoadMapStep] = Field(description="Ordered list of steps that make up the roadmap")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class LearningResource(BaseModel):
    url: List[str] = Field(description="Direct links to the most relevant learning resources")
    resource_type: Literal["official_documentation", "book", "online_video_course", "paper"] = Field(
        description="Resource type limited to official documentation, books, online video courses, article, or papers"
    )
class LearningResourceList(BaseModel):
    learning_resources: List[LearningResource] = Field(description="List of learning resources")
