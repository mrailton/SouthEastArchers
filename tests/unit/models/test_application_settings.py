from app.models import Setting


def test_create_setting(app):
    """Test creating a setting"""
    from app import db

    setting = Setting(key="test_key", value="test_value")
    db.session.add(setting)
    db.session.commit()

    assert setting.key == "test_key"
    assert setting.value == "test_value"
    assert setting.updated_at is not None


def test_setting_repr(app):
    """Test setting repr"""
    from app import db

    setting = Setting(key="test_key", value="test_value")
    db.session.add(setting)
    db.session.commit()

    repr_str = repr(setting)
    assert "test_key" in repr_str
    assert "test_value" in repr_str


def test_setting_update(app):
    """Test updating a setting"""
    from app import db

    setting = Setting(key="test_key", value="initial_value")
    db.session.add(setting)
    db.session.commit()

    setting.value = "updated_value"
    db.session.commit()

    # Fetch again to verify
    updated = Setting.query.get("test_key")
    assert updated.value == "updated_value"


def test_setting_with_none_value(app):
    """Test setting with None value"""
    from app import db

    setting = Setting(key="null_key", value=None)
    db.session.add(setting)
    db.session.commit()

    fetched = Setting.query.get("null_key")
    assert fetched.value is None


def test_multiple_settings(app):
    """Test creating multiple settings"""
    from app import db

    settings = [
        Setting(key="key1", value="value1"),
        Setting(key="key2", value="value2"),
        Setting(key="key3", value="value3"),
    ]
    db.session.add_all(settings)
    db.session.commit()

    assert Setting.query.count() >= 3
