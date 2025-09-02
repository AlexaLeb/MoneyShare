from repositories.users_repo import SQLModelUsersRepo
from models.users import User


def test_users_crud(session):
    repo = SQLModelUsersRepo(session)

    # create
    u1 = repo.create(id=111, username="vasya", first_name="Вася")
    assert isinstance(u1, User)
    assert u1.id == 111

    # get
    u_loaded = repo.get(111)
    assert u_loaded is not None
    assert u_loaded.username == "vasya"

    # update
    ok = repo.update(id=111, username="vasya_new")
    assert ok is True
    assert repo.get(111).username == "vasya_new"

    # list
    u2 = repo.create(id=222, username="petya", first_name="Петя")
    users = repo.list(limit=10, offset=0)
    assert len(users) == 2
    ids = sorted([u.id for u in users])
    assert ids == [111, 222]

    # delete
    ok = repo.delete(111)
    assert ok is True
    assert repo.get(111) is None
