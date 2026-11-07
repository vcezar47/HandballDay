from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..schemas import FixtureCreate, FixtureDetail, FixtureUpdate, ScanOut, ScanRequest, VenueZoneOut
from ..security.access import require_role
from ..services import StaffService

router = APIRouter(prefix="/api/staff", tags=["staff"])
# Admins scan at any club; running a club's fixtures is staff-only until the admin panel (M5).
staff_only = Depends(require_role("staff"))


@router.get("/zones", response_model=list[VenueZoneOut])
def zones(user: User = staff_only, db: Session = Depends(get_db)):
    return StaffService(db).venue_zones(user)


@router.get("/fixtures", response_model=list[FixtureDetail])
def list_fixtures(user: User = staff_only, db: Session = Depends(get_db)):
    return StaffService(db).list_fixtures(user)


@router.post("/fixtures", response_model=FixtureDetail, status_code=status.HTTP_201_CREATED)
def create_fixture(payload: FixtureCreate, user: User = staff_only, db: Session = Depends(get_db)):
    return StaffService(db).create_fixture(user, payload)


@router.patch("/fixtures/{fixture_id}", response_model=FixtureDetail)
def update_fixture(fixture_id: int, payload: FixtureUpdate, user: User = staff_only, db: Session = Depends(get_db)):
    return StaffService(db).update_fixture(user, fixture_id, payload)


@router.post("/scan", response_model=ScanOut)
def scan(payload: ScanRequest, user: User = Depends(require_role("staff", "admin")), db: Session = Depends(get_db)):
    return StaffService(db).scan(user, payload.code)
