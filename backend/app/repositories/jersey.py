from sqlalchemy import exists, select, update

from ..models import Club, Fixture, JerseyDesign, JerseyItem, JerseyTemplate, Order, OrderStatus, Upload, User
from .base import SqlRepository


class UploadRepository(SqlRepository[Upload]):
    model = Upload

    def list_with_owner(self) -> list[tuple[Upload, str, bool]]:
        """Newest first, with the owner's email and whether a jersey design still uses the file."""
        used = exists().where(JerseyDesign.logo_upload_id == Upload.id)
        q = select(Upload, User.email, used).join(User, User.id == Upload.user_id).order_by(Upload.id.desc())
        return [tuple(row) for row in self.db.execute(q)]

    def detach(self, upload_id: int) -> None:
        """Designs that used this logo stay, without a logo."""
        self.db.execute(update(JerseyDesign).where(JerseyDesign.logo_upload_id == upload_id).values(logo_upload_id=None))


class JerseyTemplateRepository(SqlRepository[JerseyTemplate]):
    model = JerseyTemplate

    def list(self) -> list[JerseyTemplate]:
        return list(self.db.scalars(select(JerseyTemplate).order_by(JerseyTemplate.id)))


class JerseyRepository(SqlRepository[JerseyItem]):
    model = JerseyItem

    def add_design(self, design: JerseyDesign) -> JerseyDesign:
        self.db.add(design)
        self.db.flush()
        return design

    def paid_for_user(self, user_id: int) -> list[tuple[JerseyItem, JerseyDesign, Club, JerseyTemplate, Fixture]]:
        q = (
            select(JerseyItem, JerseyDesign, Club, JerseyTemplate, Fixture)
            .join(Order, Order.id == JerseyItem.order_id)
            .join(JerseyDesign, JerseyDesign.id == JerseyItem.design_id)
            .join(Club, Club.id == JerseyDesign.club_id)
            .join(JerseyTemplate, JerseyTemplate.id == JerseyDesign.template_id)
            .join(Fixture, Fixture.id == JerseyItem.fixture_id)
            .where(Order.user_id == user_id, Order.status == OrderStatus.PAID)
            .order_by(Fixture.kickoff_at, JerseyItem.id)
        )
        return [tuple(row) for row in self.db.execute(q)]
