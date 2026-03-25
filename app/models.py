from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class AudioClip(Base):
    __tablename__ = "audio_clips"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    genre = Column(String(100), nullable=False)
    duration = Column(String(20), nullable=False)
    audio_url = Column(Text, nullable=False)
    play_count = Column(Integer, nullable=False, default=0)
