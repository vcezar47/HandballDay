"""Logo uploads. Nothing a user sends is stored as sent: it is decoded and drawn again as a new WebP."""

import secrets
from abc import ABC, abstractmethod
from io import BytesIO

from PIL import Image
from sqlalchemy.orm import Session

from ..activity import log_activity
from ..config import get_config
from ..errors import AppValidationError, NotFoundError
from ..models import Upload, User
from ..repositories import UploadRepository
from ..security.access import ensure_owner

MAX_UPLOAD_BYTES = 12 * 1024 * 1024  # barem 9.04
MAX_PIXELS = 25_000_000  # a small file can still decode to a huge bitmap
LOGO_SIDE = 512
EXTENSIONS = {"png": "PNG", "jpg": "JPEG", "jpeg": "JPEG", "webp": "WEBP"}  # barem 9.05


class FileValidator(ABC):
    @abstractmethod
    def clean(self, filename: str, data: bytes) -> bytes:
        """Return a safe version of the file, or raise AppValidationError."""


class ImageValidator(FileValidator):
    """Checks the name and the real content, then rebuilds the image (barem 9.05, 10.03).

    The output is decoded pixels re-encoded as lossy WebP: metadata, appended bytes and low-bit
    (LSB) payloads do not survive. That is a strong mitigation, not a proof.
    """

    def clean(self, filename: str, data: bytes) -> bytes:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in EXTENSIONS:
            raise AppValidationError("Only PNG, JPG and WebP images are allowed")
        try:
            image = Image.open(BytesIO(data), formats=sorted(set(EXTENSIONS.values())))
            if image.format != EXTENSIONS[ext]:
                raise AppValidationError("The file content does not match its extension")
            if image.width * image.height > MAX_PIXELS:
                raise AppValidationError("The image is too large (more than 25 megapixels)")
            image.load()  # full decode: truncated or corrupt files fail here
            rgba = image.convert("RGBA")
        except AppValidationError:
            raise
        except (OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
            raise AppValidationError("That file is not a valid image") from exc
        # A new image built from the raw pixels carries no EXIF, ICC profile or text chunks.
        fresh = Image.frombytes("RGBA", rgba.size, rgba.tobytes())
        fresh.thumbnail((LOGO_SIDE, LOGO_SIDE))
        out = BytesIO()
        fresh.save(out, "WEBP", quality=80, method=4)
        return out.getvalue()


class UploadService:
    def __init__(self, db: Session, validator: FileValidator | None = None) -> None:
        self.db = db
        self.validator = validator or ImageValidator()
        self.uploads = UploadRepository(db)

    def save(self, user: User, filename: str, data: bytes) -> Upload:
        try:
            clean = self.validator.clean(filename, data)
        except AppValidationError:
            log_activity("upload_rejected", user_id=user.id, size=len(data))
            raise
        # Random name: the client's filename is never used on disk, so it cannot point anywhere.
        stored = secrets.token_hex(16) + ".webp"
        upload = self.uploads.add(Upload(user_id=user.id, stored_name=stored, mime="image/webp", size_bytes=len(clean)))
        directory = get_config().upload_dir
        directory.mkdir(parents=True, exist_ok=True)
        (directory / stored).write_bytes(clean)
        self.db.commit()
        log_activity("upload_ok", user_id=user.id, upload_id=upload.id, size=len(clean))
        return upload

    def path_for(self, user: User, upload_id: int):
        """The file of an upload, for its owner (or an admin) only."""
        upload = self.uploads.get(upload_id)
        if upload is None:
            raise NotFoundError("Upload not found")
        ensure_owner(user, upload.user_id)
        path = get_config().upload_dir / upload.stored_name
        if not path.is_file():
            raise NotFoundError("Upload not found")
        return path

