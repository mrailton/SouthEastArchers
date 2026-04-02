from app.repositories import SettingsRepository


def test_settings_repository_get_value(app):
    result = SettingsRepository.get_value("nonexistent")
    assert result is None


def test_settings_repository_set_and_get(app):
    SettingsRepository.set_value("test_key", "test_value")
    SettingsRepository.save()
    assert SettingsRepository.get_value("test_key") == "test_value"
