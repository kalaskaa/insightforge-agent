from pydantic import BaseModel, Field


class ResearchTestRequest(BaseModel):
    brief: str = Field(min_length=10, max_length=500)


class ResearchTestResponse(BaseModel):
    brief: str
    response: str


class ResearchGraphRequest(BaseModel):
    brief: str = Field(min_length=10, max_length=500)


class ResearchGraphResponse(BaseModel):
    brief: str
    plan: str
    research: str
    status: str


class ResearchAgentRequest(BaseModel):
    brief: str = Field(min_length=10, max_length=500)


class ResearchAgentResponse(BaseModel):
    brief: str
    response: str