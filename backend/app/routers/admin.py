from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..schemas import ClubOut
from ..schemas.admin import ActivityEntry, AdminUploadOut, AdminUserOut, AdminUserUpdate, ClubUpdate
from ..security.access import require_role
from ..services.admin import AdminService

router = APIRouter(prefix="/api/admin", tags=["admin"])
admin_only = Depends(require_role("admin"))


@router.get("/users", response_model=list[AdminUserOut])
def users(_: User = admin_only, db: Session = Depends(get_db)):
    return AdminService(db).list_users()


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def set_role(user_id: int, payload: AdminUserUpdate, admin: User = admin_only, db: Session = Depends(get_db)):
    return AdminService(db).set_role(admin, user_id, payload)


@router.patch("/clubs/{slug}", response_model=ClubOut)
def update_club(slug: str, payload: ClubUpdate, admin: User = admin_only, db: Session = Depends(get_db)):
    return AdminService(db).update_club(admin, slug, payload)


@router.get("/uploads", response_model=list[AdminUploadOut])
def uploads(_: User = admin_only, db: Session = Depends(get_db)):
    return AdminService(db).list_uploads()


@router.delete("/uploads/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_upload(upload_id: int, admin: User = admin_only, db: Session = Depends(get_db)):
    AdminService(db).delete_upload(admin, upload_id)


@router.get("/activity", response_model=list[ActivityEntry])
def activity(
    limit: int = Query(200, ge=1, le=500), event: str | None = Query(None, max_length=50),
    _: User = admin_only, db: Session = Depends(get_db),
):
    return AdminService(db).activity(limit, event)
