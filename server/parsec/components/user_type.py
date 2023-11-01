# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from parsec._parsec import (
    DateTime,
    DeviceCertificate,
    DeviceID,
    DeviceLabel,
    DeviceName,
    HumanHandle,
    PublicKey,
    UserCertificate,
    UserID,
    UserProfile,
    VerifyKey,
)

LastCertificateIndex = int


@dataclass(slots=True)
class RequireGreaterTimestamp:
    strictly_greater_than: DateTime


class CertificateValidationError(Exception):
    def __init__(self, status: str, reason: str) -> None:
        self.status = status
        self.reason = reason
        super().__init__((status, reason))


CertificateValidationBadOutcome = Enum(
    "CertificateValidationBadOutcome",
    (
        "INVALID_CERTIFICATE",
        "TIMESTAMP_MISMATCH",
        "TIMESTAMP_OUT_OF_BALLPARK",
        "USER_ID_MISMATCH",
        "INVALID_REDACTED",
        "REDACTED_MISMATCH",
    ),
)


@dataclass(slots=True)
class Device:
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.device_id.str})"

    @property
    def device_name(self) -> DeviceName:
        return self.device_id.device_name

    @property
    def user_id(self) -> UserID:
        return self.device_id.user_id

    @property
    def verify_key(self) -> VerifyKey:
        return DeviceCertificate.unsecure_load(self.device_certificate).verify_key

    device_id: DeviceID
    device_label: DeviceLabel
    device_certificate: bytes
    redacted_device_certificate: bytes
    device_certifier: DeviceID | None
    created_on: DateTime = field(default_factory=DateTime.now)


@dataclass(slots=True)
class User:
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.user_id.str})"

    def is_revoked(self) -> bool:
        return self.revoked_on is not None

    @property
    def public_key(self) -> PublicKey:
        return UserCertificate.unsecure_load(self.user_certificate).public_key

    @property
    def profile(self) -> UserProfile:
        if self.updates:
            return self.updates[-1].new_profile
        else:
            return self.initial_profile

    user_id: UserID
    human_handle: HumanHandle
    user_certificate: bytes
    redacted_user_certificate: bytes
    user_certifier: DeviceID | None
    initial_profile: UserProfile = UserProfile.STANDARD
    created_on: DateTime = field(default_factory=DateTime.now)
    revoked_on: DateTime | None = None
    revoked_user_certificate: bytes | None = None
    revoked_user_certifier: DeviceID | None = None
    updates: tuple[UserUpdate, ...] = ()


@dataclass(slots=True)
class UserUpdate:
    new_profile: UserProfile
    updated_on: DateTime
    user_update_certificate: bytes
    user_update_certifier: DeviceID | None
