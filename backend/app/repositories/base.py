from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """What services may rely on, whatever the storage is."""

    @abstractmethod
    def get(self, id: int) -> T | None: ...

    @abstractmethod
    def list(self) -> list[T]: ...

    @abstractmethod
    def add(self, entity: T) -> T: ...

    @abstractmethod
    def delete(self, entity: T) -> None: ...


class SqlRepository(IRepository[T]):
    """SQLAlchemy implementation. Subclasses set `model` and add their own queries.

    Repositories flush but never commit: the service owns the transaction.
    """

    model: type[T]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id: int) -> T | None:
        return self.db.get(self.model, id)

    def list(self) -> list[T]:
        return list(self.db.scalars(select(self.model)))

    def add(self, entity: T) -> T:
        self.db.add(entity)
        self.db.flush()
        return entity

    def delete(self, entity: T) -> None:
        self.db.delete(entity)
        self.db.flush()
