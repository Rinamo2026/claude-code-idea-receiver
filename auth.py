"""WebAuthn パスキー認証"""
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone

from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    ResidentKeyRequirement,
    PublicKeyCredentialDescriptor,
    AuthenticatorTransport,
)
from webauthn.helpers import bytes_to_base64url, base64url_to_bytes

import config
import models

# チャレンジの一時保存 (TTL 5分)
_challenges: dict[str, tuple[bytes, float]] = {}
CHALLENGE_TTL = 300


def _store_challenge(key: str, challenge: bytes):
    _challenges[key] = (challenge, time.time())
    # 古いチャレンジを掃除
    now = time.time()
    expired = [k for k, (_, t) in _challenges.items() if now - t > CHALLENGE_TTL]
    for k in expired:
        del _challenges[k]


def _get_challenge(key: str) -> bytes | None:
    entry = _challenges.pop(key, None)
    if not entry:
        return None
    challenge, ts = entry
    if time.time() - ts > CHALLENGE_TTL:
        return None
    return challenge


async def get_registration_options(user_name: str = "owner") -> dict:
    """パスキー登録オプション生成"""
    user_id = "owner"

    # 既存クレデンシャルを除外リストに
    existing = await models.get_user_credentials(user_id)
    exclude = [
        PublicKeyCredentialDescriptor(id=cred["credential_id"])
        for cred in existing
    ]

    options = generate_registration_options(
        rp_id=config.RP_ID,
        rp_name=config.RP_NAME,
        user_id=user_id.encode(),
        user_name=user_name,
        user_display_name=user_name,
        exclude_credentials=exclude,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
            resident_key=ResidentKeyRequirement.PREFERRED,
        ),
    )

    _store_challenge("reg:" + user_id, options.challenge)
    return options_to_json(options)


async def verify_registration(credential_json: dict) -> bool:
    """パスキー登録検証"""
    user_id = "owner"
    challenge = _get_challenge("reg:" + user_id)
    if not challenge:
        raise ValueError("Challenge expired or not found")

    verification = verify_registration_response(
        credential=credential_json,
        expected_challenge=challenge,
        expected_rp_id=config.RP_ID,
        expected_origin=config.ORIGIN,
    )

    await models.insert_user(user_id, "owner")
    await models.insert_credential(
        credential_id=verification.credential_id,
        user_id=user_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
    )
    return True


async def get_authentication_options() -> dict:
    """パスキー認証オプション生成"""
    user_id = "owner"
    creds = await models.get_user_credentials(user_id)

    allow = [
        PublicKeyCredentialDescriptor(id=cred["credential_id"])
        for cred in creds
    ]

    options = generate_authentication_options(
        rp_id=config.RP_ID,
        allow_credentials=allow if allow else None,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    _store_challenge("auth:" + user_id, options.challenge)
    return options_to_json(options)


async def verify_authentication(credential_json: dict) -> str:
    """パスキー認証検証。セッションIDを返す。"""
    user_id = "owner"
    challenge = _get_challenge("auth:" + user_id)
    if not challenge:
        raise ValueError("Challenge expired or not found")

    cred_id = base64url_to_bytes(credential_json.get("id", ""))
    stored = await models.get_credential(cred_id)
    if not stored:
        raise ValueError("Unknown credential")

    verification = verify_authentication_response(
        credential=credential_json,
        expected_challenge=challenge,
        expected_rp_id=config.RP_ID,
        expected_origin=config.ORIGIN,
        credential_public_key=stored["public_key"],
        credential_current_sign_count=stored["sign_count"],
    )

    await models.update_sign_count(cred_id, verification.new_sign_count)

    # セッション発行
    session_id = secrets.token_urlsafe(32)
    expires = (datetime.now(tz=timezone.utc) + timedelta(seconds=config.SESSION_MAX_AGE)).strftime("%Y-%m-%d %H:%M:%S")
    await models.insert_session(session_id, user_id, expires)

    return session_id
