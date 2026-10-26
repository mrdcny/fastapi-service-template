import pytest

from fastapi_service_template.config import Settings


def test_reads_prefixed_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("APP_PORT", "9000")
    settings = Settings(_env_file=None)
    assert settings.log_level == "DEBUG"
    assert settings.port == 9000


def test_database_password_is_not_leaked_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_DATABASE_URL", "postgresql+asyncpg://app:hunter2@db/app")
    settings = Settings(_env_file=None)
    assert "hunter2" not in repr(settings)
    assert "hunter2" in settings.database_url.get_secret_value()


def test_rejects_invalid_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_LOG_LEVEL", "LOUD")
    with pytest.raises(ValueError, match="log_level"):
        Settings(_env_file=None)
