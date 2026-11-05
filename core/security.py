
import hashlib
import secrets
import hmac


def generate_token():
    return secrets.token_urlsafe(32)


def calculate_sha256(file_path):
    digest = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):
            digest.update(chunk)

    return digest.hexdigest()


def verify_sha256(file_path, expected):
    actual = calculate_sha256(file_path)

    return hmac.compare_digest(
        actual.lower(),
        expected.lower()
    )
