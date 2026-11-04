from sqlalchemy.orm import Session

from ..db import ensure_database, get_engine
from ..models import Base
from . import seed_all

ensure_database()
Base.metadata.create_all(get_engine())
with Session(get_engine()) as db:
    seed_all(db)
print("Seeded.")
