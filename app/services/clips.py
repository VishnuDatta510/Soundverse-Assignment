import httpx
from sqlalchemy.orm import Session
from app.models import AudioClip
from app.schemas import ClipCreate
from app.seed_data import SEED_CLIPS


def seed_clips(db: Session) -> None:
    if db.query(AudioClip).count() > 0:
        return
    for data in SEED_CLIPS:
        db.add(AudioClip(**data))
    db.commit()


def get_all_clips(db: Session) -> list[AudioClip]:
    return db.query(AudioClip).all()


def get_clip_by_id(db: Session, clip_id: int) -> AudioClip | None:
    return db.query(AudioClip).filter(AudioClip.id == clip_id).first()


def create_clip(db: Session, payload: ClipCreate) -> AudioClip:
    data = payload.model_dump()
    data["audio_url"] = str(data["audio_url"])
    clip = AudioClip(**data)
    db.add(clip)
    db.commit()
    db.refresh(clip)
    return clip


def increment_play_count(db: Session, clip_id: int) -> None:
    db.query(AudioClip).filter(AudioClip.id == clip_id).update(
        {AudioClip.play_count: AudioClip.play_count + 1}
    )
    db.commit()


async def iter_remote_audio(url: str):
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size=65536):
                yield chunk
