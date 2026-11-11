from sqlalchemy.orm import Session

from ..models import User
from ..repositories import JerseyRepository, JerseyTemplateRepository
from ..schemas import ClubSummary, FixtureOut, JerseyOut, TemplateOut, TemplatesOut
from ..schemas.jersey import SIZES
from .orders import JERSEY_PRICE_BANI


class JerseyService:
    def __init__(self, db: Session) -> None:
        self.templates = JerseyTemplateRepository(db)
        self.jerseys = JerseyRepository(db)

    def catalog(self) -> TemplatesOut:
        return TemplatesOut(
            price_bani=JERSEY_PRICE_BANI, sizes=list(SIZES),
            templates=[TemplateOut.model_validate(t) for t in self.templates.list()],
        )

    def mine(self, user: User) -> list[JerseyOut]:
        return [
            JerseyOut(
                id=item.id, size=item.size, price_bani=item.price_bani, club=ClubSummary.model_validate(club),
                template=template.svg_key, primary_color=design.primary_color, secondary_color=design.secondary_color,
                name_text=design.name_text, number=design.number, logo_upload_id=design.logo_upload_id,
                pickup=FixtureOut.model_validate(fixture),
            )
            for item, design, club, template, fixture in self.jerseys.paid_for_user(user.id)
        ]
