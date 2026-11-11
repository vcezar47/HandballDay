from sqlalchemy.orm import Session

from ..activity import log_activity, read_activity
from ..config import get_config
from ..errors import AppValidationError, ConflictError, NotFoundError
from ..models import User
from ..repositories import ClubRepository, RoleRepository, UploadRepository, UserRepository
from ..repositories.jersey import JerseyRepository
from ..schemas import ClubOut
from ..schemas.admin import ActivityEntry, AdminUploadOut, AdminUserOut, AdminUserUpdate, ClubUpdate
from .catalog import CatalogService


class AdminService:
    """UC7: users and roles, club details, upload moderation, the activity log. Routes are admin-only."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.clubs = ClubRepository(db)
        self.uploads = UploadRepository(db)
        self.jerseys = JerseyRepository(db)

    def list_users(self) -> list[AdminUserOut]:
        return [
            AdminUserOut(id=u.id, email=u.email, display_name=u.display_name, role=u.role.name, club=slug, created_at=u.created_at)
            for u, slug in self.users.list_with_club()
        ]

    def set_role(self, admin: User, user_id: int, payload: AdminUserUpdate) -> AdminUserOut:
        if user_id == admin.id:
            raise ConflictError("You cannot change your own role, so the site is never left without an admin")
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        club = None
        if payload.role == "staff":
            club = self.clubs.get_by_slug(payload.club or "")
            if club is None:
                raise AppValidationError("Staff need a club")
        user.role_id = self.roles.get_by_name(payload.role).id
        user.club_id = club.id if club else None  # only staff belong to a club
        self.db.commit()
        log_activity("role_changed", admin_id=admin.id, user_id=user.id, role=payload.role, club=club.slug if club else None)
        return next(u for u in self.list_users() if u.id == user_id)

    def update_club(self, admin: User, slug: str, payload: ClubUpdate) -> ClubOut:
        club = self.clubs.get_by_slug(slug)
        if club is None:
            raise NotFoundError("Club not found")
        changes = payload.model_dump(exclude_none=True)
        for field, value in changes.items():
            setattr(club, field, value.lower() if field.endswith("_color") else value)
        self.db.commit()
        log_activity("club_updated", admin_id=admin.id, club=slug, fields=sorted(changes))
        return CatalogService(self.db).get_club(slug)

    def list_uploads(self) -> list[AdminUploadOut]:
        return [
            AdminUploadOut(id=u.id, owner_email=email, size_bytes=u.size_bytes, created_at=u.created_at, in_use=used)
            for u, email, used in self.uploads.list_with_owner()
        ]

    def delete_upload(self, admin: User, upload_id: int) -> None:
        upload = self.uploads.get(upload_id)
        if upload is None:
            raise NotFoundError("Upload not found")
        self.uploads.detach(upload_id)
        (get_config().upload_dir / upload.stored_name).unlink(missing_ok=True)
        self.uploads.delete(upload)
        self.db.commit()
        log_activity("upload_removed", admin_id=admin.id, upload_id=upload_id, owner_id=upload.user_id)

    def activity(self, limit: int, event: str | None) -> list[ActivityEntry]:
        return [ActivityEntry(**e) for e in read_activity(limit, event)]
