from fastapi import APIRouter, Depends, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from urllib.parse import unquote

from ..db import get_db
from ..errors import PayloadTooLargeError
from ..limits import UPLOAD, limiter
from ..models import User
from ..schemas import JerseyOut, TemplatesOut, UploadOut
from ..security.access import current_user
from ..security.captcha import CaptchaVerifier, get_captcha
from ..services import JerseyService, UploadService
from ..services.uploads import MAX_UPLOAD_BYTES

router = APIRouter(prefix="/api", tags=["jersey"])
TOO_LARGE = f"Files can be at most {MAX_UPLOAD_BYTES // (1024 * 1024)} MB"


@router.get("/jersey-templates", response_model=TemplatesOut)
def templates(db: Session = Depends(get_db)):
    return JerseyService(db).catalog()


@router.get("/jerseys", response_model=list[JerseyOut])
def my_jerseys(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return JerseyService(db).mine(user)


@router.post("/uploads", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(UPLOAD)
async def upload(
    request: Request, user: User = Depends(current_user), db: Session = Depends(get_db),
    captcha: CaptchaVerifier = Depends(get_captcha),
):
    """The file is the raw request body (the name travels in X-Filename), so it can be counted as it arrives."""
    # Before reading the body: a bot should not get to push 12 MB at us. The check calls Cloudflare, so it runs in a thread.
    await run_in_threadpool(captcha.check, request.headers.get("x-captcha-token"), request.client.host if request.client else None)
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > MAX_UPLOAD_BYTES:
        raise PayloadTooLargeError(TOO_LARGE)  # cheap early refusal; the header may lie, so the loop checks too
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_UPLOAD_BYTES:
            raise PayloadTooLargeError(TOO_LARGE)
        chunks.append(chunk)
    return UploadService(db).save(user, unquote(request.headers.get("x-filename", "")), b"".join(chunks))


@router.get("/uploads/{upload_id}")
def get_upload(upload_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    path = UploadService(db).path_for(user, upload_id)
    return FileResponse(path, media_type="image/webp", headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, max-age=3600"})
