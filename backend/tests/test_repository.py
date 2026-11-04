import pytest

from app.main import app
from app.models import Role
from app.repositories import IRepository, RoleRepository


def test_interface_cannot_be_instantiated():
    with pytest.raises(TypeError):
        IRepository()


def test_repository_add_get_list_delete(db):
    repo = RoleRepository(db)
    role = repo.add(Role(name="referee"))
    assert repo.get(role.id) is role
    assert repo.get_by_name("referee") is role
    assert "referee" in [r.name for r in repo.list()]
    repo.delete(role)
    assert repo.get_by_name("referee") is None


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert app.title == "HandballDay API"
