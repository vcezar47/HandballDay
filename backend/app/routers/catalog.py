from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import ClubOut, ClubSummary, FixtureDetail, FixtureOut
from ..services import CatalogService

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/clubs", response_model=list[ClubSummary])
def list_clubs(db: Session = Depends(get_db)):
    return CatalogService(db).list_clubs()


@router.get("/clubs/{slug}", response_model=ClubOut)
def get_club(slug: str, db: Session = Depends(get_db)):
    return CatalogService(db).get_club(slug)


@router.get("/fixtures", response_model=list[FixtureOut])
def list_fixtures(
    club: str | None = Query(None, max_length=100, description="club slug"),
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return CatalogService(db).list_fixtures(club, date_from, date_to, limit)


@router.get("/fixtures/{fixture_id}", response_model=FixtureDetail)
def get_fixture(fixture_id: int, db: Session = Depends(get_db)):
    return CatalogService(db).get_fixture(fixture_id)
