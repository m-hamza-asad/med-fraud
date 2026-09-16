import pytest

from medfraud.auth import hash_password, verify_password


def test_password_hash_is_salted_and_verifiable():
    first = hash_password("CorrectHorse!2026")
    second = hash_password("CorrectHorse!2026")
    assert first != second
    assert verify_password(first, "CorrectHorse!2026")
    assert not verify_password(first, "wrong-password")


def test_short_password_rejected():
    with pytest.raises(ValueError): hash_password("too-short")

