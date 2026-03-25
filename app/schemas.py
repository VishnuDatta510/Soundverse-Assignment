from pydantic import BaseModel, HttpUrl, Field


class ClipBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    genre: str = Field(..., min_length=1, max_length=100)
    duration: str = Field(..., examples=["30s"])
    audio_url: HttpUrl


class ClipCreate(ClipBase):
    pass


class ClipResponse(ClipBase):
    id: int
    audio_url: str
    model_config = {"from_attributes": True}


class ClipStats(BaseModel):
    id: int
    title: str
    description: str | None
    genre: str
    duration: str
    audio_url: str
    play_count: int
    model_config = {"from_attributes": True}
