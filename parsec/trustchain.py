from typing import Tuple
import pendulum
from pendulum import Pendulum
from json import JSONDecodeError

from parsec.types import DeviceID, UserID
from parsec.schema import ValidationError, UnknownCheckedSchema, fields
from parsec.crypto import (
    CryptoError,
    VerifyKey,
    SigningKey,
    PublicKey,
    sign_and_add_meta,
    verify_signature_from,
    unsecure_extract_msg_from_signed,
    decode_signedmeta,
)


class TrustChainError(Exception):
    pass


class TrustChainInvalidDataError(TrustChainError):
    pass


class TrustChainTooOldError(TrustChainError):
    pass


class TrustChainBrokenChainError(TrustChainError):
    pass


ROOT_DEVICE_ID = DeviceID("root@root")

# TODO: configurable ?
MAX_TS_BALLPARK = 30 * 60


def timestamps_in_the_ballpark(ts1: Pendulum, ts2: Pendulum) -> bool:
    """
    Useful to compare timestamp provided inside the certified payload and
    the one generated by the backend when it received the certified payload.
    """
    return abs((ts1 - ts2).total_seconds()) < MAX_TS_BALLPARK


class CertifiedDeviceSchema(UnknownCheckedSchema):
    type = fields.CheckedConstant("device", required=True)
    timestamp = fields.DateTime(required=True)
    device_id = fields.DeviceID(required=True)
    verify_key = fields.VerifyKey(required=True)


class CertifiedUserSchema(UnknownCheckedSchema):
    type = fields.CheckedConstant("user", required=True)
    timestamp = fields.DateTime(required=True)
    user_id = fields.UserID(required=True)
    public_key = fields.PublicKey(required=True)


class CertifiedDeviceRevocationSchema(UnknownCheckedSchema):
    type = fields.CheckedConstant("device_revocation", required=True)
    timestamp = fields.DateTime(required=True)
    device_id = fields.DeviceID(required=True)


certified_device_schema = CertifiedDeviceSchema(strict=True)
certified_user_schema = CertifiedUserSchema(strict=True)
certified_device_revocation_schema = CertifiedDeviceRevocationSchema(strict=True)


def _validate_certified_payload(
    schema: UnknownCheckedSchema, certifier_key: VerifyKey, payload: bytes, now: Pendulum = None
) -> dict:
    """
    Raises:
        TrustChainInvalidDataError
        TrustChainTooOldError
    """
    try:
        raw = verify_signature_from(certifier_key, payload)
        data = schema.loads(raw.decode("utf8")).data

    except (CryptoError, ValidationError, JSONDecodeError, ValueError) as exc:
        raise TrustChainInvalidDataError(*exc.args) from exc

    if not timestamps_in_the_ballpark(data["timestamp"], now or pendulum.now()):
        raise TrustChainTooOldError("Timestamp is too old.")

    return data


def certify_device(
    certifier_id: DeviceID,
    certifier_key: SigningKey,
    device_id: DeviceID,
    verify_key: VerifyKey,
    now: Pendulum = None,
) -> bytes:
    """
    Raises:
        TrustChainInvalidDataError
    """
    try:
        payload = certified_device_schema.dumps(
            {
                "type": "device",
                "timestamp": now or pendulum.now(),
                "device_id": device_id,
                "verify_key": verify_key,
            }
        ).data.encode("utf8")
        return sign_and_add_meta(certifier_id, certifier_key, payload)

    except (CryptoError, ValidationError, JSONDecodeError, ValueError) as exc:
        raise TrustChainInvalidDataError(*exc.args) from exc


def validate_payload_certified_device(
    certifier_key: VerifyKey, payload: bytes, now: Pendulum
) -> dict:
    """
    Raises:
        TrustChainInvalidDataError
        TrustChainTooOldError
    """
    return _validate_certified_payload(certified_device_schema, certifier_key, payload, now)


def unsecure_certified_device_extract_verify_key(data: bytes) -> VerifyKey:
    """
    Raises:
        TrustChainInvalidDataError
    """
    try:
        _, signed = decode_signedmeta(data)
        raw = unsecure_extract_msg_from_signed(signed)
        return certified_device_schema.loads(raw.decode("utf8")).data["verify_key"]

    except (CryptoError, ValidationError, JSONDecodeError, ValueError) as exc:
        raise TrustChainInvalidDataError(*exc.args) from exc


def certify_user(
    certifier_id: DeviceID,
    certifier_key: SigningKey,
    user_id: UserID,
    public_key: PublicKey,
    now: Pendulum = None,
) -> bytes:
    """
    Raises:
        TrustChainInvalidDataError
    """
    try:
        payload = certified_user_schema.dumps(
            {
                "type": "user",
                "timestamp": now or pendulum.now(),
                "user_id": user_id,
                "public_key": public_key,
            }
        ).data.encode("utf8")
        return sign_and_add_meta(certifier_id, certifier_key, payload)

    except (CryptoError, ValidationError, JSONDecodeError, ValueError) as exc:
        raise TrustChainInvalidDataError(*exc.args) from exc


def validate_payload_certified_user(
    certifier_key: VerifyKey, payload: bytes, now: Pendulum
) -> dict:
    """
    Raises:
        TrustChainInvalidDataError
        TrustChainTooOldError
    """
    return _validate_certified_payload(certified_user_schema, certifier_key, payload, now)


def unsecure_certified_user_extract_public_key(data: bytes) -> PublicKey:
    """
    Raises:
        TrustChainInvalidDataError
    """
    try:
        _, signed = decode_signedmeta(data)
        raw = unsecure_extract_msg_from_signed(signed)
        return certified_user_schema.loads(raw.decode("utf8")).data["public_key"]

    except (CryptoError, ValidationError, JSONDecodeError, ValueError) as exc:
        raise TrustChainInvalidDataError(*exc.args) from exc


def certify_device_revocation(
    certifier_id: DeviceID,
    certifier_key: SigningKey,
    revoked_device_id: DeviceID,
    now: Pendulum = None,
) -> bytes:
    """
    Raises:
        TrustChainInvalidDataError
    """
    try:
        payload = certified_device_revocation_schema.dumps(
            {
                "type": "device_revocation",
                "timestamp": now or pendulum.now(),
                "device_id": revoked_device_id,
            }
        ).data.encode("utf8")
        return sign_and_add_meta(certifier_id, certifier_key, payload)

    except (CryptoError, ValidationError, JSONDecodeError, ValueError) as exc:
        raise TrustChainInvalidDataError(*exc.args) from exc


def validate_payload_certified_device_revocation(
    certifier_key: VerifyKey, payload: bytes, now: Pendulum
) -> dict:
    """
    Raises:
        TrustChainInvalidDataError
        TrustChainTooOldError
    """
    return _validate_certified_payload(
        certified_device_revocation_schema, certifier_key, payload, now
    )


def certified_extract_parts(certified: bytes) -> Tuple[DeviceID, bytes]:
    """
    Raises:
        TrustChainInvalidDataError
    Returns: Tuple of certifier device id and payload
    """
    try:
        return decode_signedmeta(certified)

    except CryptoError as exc:
        raise TrustChainInvalidDataError(*exc.args) from exc


def cascade_validate_devices(
    certified_devices, root_verify_key, root_device_id=ROOT_DEVICE_ID
) -> Tuple[dict]:
    """
    Raises:
        TrustChainBrokenChainError
        TrustChainInvalidDataError
        TrustChainTooOldError
    """
    devices = []
    for certified_device in reversed(certified_devices):
        certifier_id, certified_payload = certified_extract_parts(certified_device)
        if not devices:
            if certifier_id != ROOT_DEVICE_ID:
                raise TrustChainError(f"Device {device} is signed {device}")  # TODO
            certifier_key = root_verify_key

        else:
            if certifier_id != devices[-1].id:
                raise TrustChainError(f"Device {device} is signed {device}")  # TODO
            certifier_key = devices[-1]["verify_key"]

        validated = validate_payload_certified_device(certifier_key, certified_payload)
        devices.append(validated)

    return tuple(reversed(devices))
