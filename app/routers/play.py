from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.database import get_db
from app.schemas import ClipCreate, ClipResponse, ClipStats
from app.services import clips as clip_service

router = APIRouter(
    prefix="/play",
    tags=["play"],
    dependencies=[Depends(require_api_key)],
)


@router.get(
    "",
    response_model=list[ClipResponse],
    summary="List all available sound clips",
)
def list_clips(db: Session = Depends(get_db)):
    return clip_service.get_all_clips(db)


@router.post(
    "",
    response_model=ClipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new sound clip (metadata only, no file upload)",
)
def add_clip(payload: ClipCreate, db: Session = Depends(get_db)):
    return clip_service.create_clip(db, payload)


@router.get(
    "/{clip_id}/stream",
    summary="Stream a clip's audio",
    response_class=StreamingResponse,
)
async def stream_clip(
    clip_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    clip = clip_service.get_clip_by_id(db, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail=f"Clip {clip_id} not found.")

    background_tasks.add_task(clip_service.increment_play_count, db, clip_id)

    return StreamingResponse(
        clip_service.iter_remote_audio(str(clip.audio_url)),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="{clip.title}.mp3"',
            "X-Clip-Id": str(clip_id),
        },
    )


@router.get(
    "/{clip_id}/stats",
    response_model=ClipStats,
    summary="Get play count and metadata for a clip",
)
def clip_stats(clip_id: int, db: Session = Depends(get_db)):
    clip = clip_service.get_clip_by_id(db, clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail=f"Clip {clip_id} not found.")
    return clip
