from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_sign_message,
    decode_token,
    generate_nonce,
    get_password_hash,
    verify_password,
)


def test_password_hash_round_trip():
    password = "SalfPassword123!"

    hashed_password = get_password_hash(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password) is True


def test_generate_nonce_returns_unique_hex_values():
    first = generate_nonce()
    second = generate_nonce()

    assert first != second
    assert len(first) == 32
    assert len(second) == 32
    int(first, 16)
    int(second, 16)


def test_create_sign_message_has_expected_format():
    address = "0x1234567890abcdef"
    nonce = "deadbeefcafebabe"

    message = create_sign_message(address, nonce)

    assert message == (
        "SALF Authentication\n\n"
        f"Address: {address}\n"
        f"Nonce: {nonce}"
    )


def test_access_token_can_be_decoded_with_access_type():
    token = create_access_token(
        {"sub": "0xabc", "role": "faculty"},
        expires_delta=timedelta(minutes=5),
    )

    payload = decode_token(token)

    assert payload["sub"] == "0xabc"
    assert payload["role"] == "faculty"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_refresh_token_can_be_decoded_with_refresh_type():
    token = create_refresh_token({"sub": "0xdef"})

    payload = decode_token(token)

    assert payload["sub"] == "0xdef"
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_token_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not-a-valid-jwt")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired token"
