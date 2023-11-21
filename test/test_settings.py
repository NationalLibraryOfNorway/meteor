"""Test that settings are loaded correctly"""

from src.settings import Settings


def test_config():
    """Test that settings are loaded correctly"""
    settings = Settings(_env_file='.env.example')
    assert settings.MOUNT_FOLDER == "/tmp/pdf_dir"
    assert settings.MAX_FILE_SIZE_MB == 123
    assert settings.ENVIRONMENT == "local"
    assert settings.LANGUAGES == "mul,eng,nob"
    assert settings.REGISTRY_FILE == ""
    assert settings.REGISTRY_HOST == ""
    assert settings.REGISTRY_USER == ""
    assert settings.REGISTRY_DATABASE == ""
    assert settings.REGISTRY_PASSWORD == ""
    assert settings.USE_GIELLADETECT is False
    assert settings.GIELLADETECT_LANGS == ""
    assert settings.CUSTOM_PATH == ""
