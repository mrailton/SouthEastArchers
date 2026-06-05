from app.repositories import RBACRepository


def test_rbac_repository_list_roles(app):
    roles = RBACRepository.list_roles()
    assert len(roles) >= 1


def test_rbac_repository_list_permissions(app):
    perms = RBACRepository.list_permissions()
    assert len(perms) >= 1


def test_rbac_repository_role_name_exists(app):
    assert RBACRepository.role_name_exists("Admin")
    assert not RBACRepository.role_name_exists("NonexistentRole")


def test_rbac_repository_get_permissions_by_ids(app):
    all_perms = RBACRepository.list_permissions()
    ids = [p.id for p in all_perms[:2]]
    result = RBACRepository.get_permissions_by_ids(ids)
    assert len(result) == 2
