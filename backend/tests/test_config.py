from app.core.config import Settings


def test_settings_accept_jwt_secret_alias():
    settings = Settings(JWT_SECRET="alias-secret", JWT_ALGORITHM="HS512")

    assert settings.SECRET_KEY == "alias-secret"
    assert settings.ALGORITHM == "HS512"


def test_settings_derive_ipfs_fields_from_api_url():
    settings = Settings(
        IPFS_API_URL="http://127.0.0.1:5999",
        IPFS_GATEWAY_URL="http://127.0.0.1:8080",
    )

    assert settings.IPFS_HOST == "127.0.0.1"
    assert settings.IPFS_PORT == 5999
    assert settings.IPFS_GATEWAY == "http://127.0.0.1:8080/ipfs/"


def test_settings_parse_debug_variants():
    assert Settings(DEBUG="true").DEBUG is True
    assert Settings(DEBUG="production").DEBUG is False
