# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

from parsec._parsec import DateTime, VerifyKey

class Req:
    def __init__(
        self,
        bootstrap_token: str,
        root_verify_key: VerifyKey,
        user_certificate: bytes,
        device_certificate: bytes,
        redacted_user_certificate: bytes,
        redacted_device_certificate: bytes,
        sequester_authority_certificate: bytes | None,
    ) -> None: ...
    def dump(self) -> bytes: ...
    @property
    def bootstrap_token(self) -> str: ...
    @property
    def root_verify_key(self) -> VerifyKey: ...
    @property
    def user_certificate(self) -> bytes: ...
    @property
    def device_certificate(self) -> bytes: ...
    @property
    def redacted_user_certificate(self) -> bytes: ...
    @property
    def redacted_device_certificate(self) -> bytes: ...
    @property
    def sequester_authority_certificate(self) -> bytes | None: ...

class Rep:
    @staticmethod
    def load(raw: bytes) -> Rep: ...
    def dump(self) -> bytes: ...

class RepUnknownStatus(Rep):
    def __init__(self, status: str, reason: str | None) -> None: ...
    @property
    def status(self) -> str: ...
    @property
    def reason(self) -> str | None: ...

class RepOk(Rep):
    def __init__(
        self,
    ) -> None: ...

class RepInvalidCertification(Rep):
    def __init__(self, reason: str | None) -> None: ...
    @property
    def reason(self) -> str | None: ...

class RepInvalidData(Rep):
    def __init__(self, reason: str | None) -> None: ...
    @property
    def reason(self) -> str | None: ...

class RepBadTimestamp(Rep):
    def __init__(
        self,
        reason: str | None,
        ballpark_client_early_offset: float,
        ballpark_client_late_offset: float,
        backend_timestamp: DateTime,
        client_timestamp: DateTime,
    ) -> None: ...
    @property
    def reason(self) -> str | None: ...
    @property
    def ballpark_client_early_offset(self) -> float: ...
    @property
    def ballpark_client_late_offset(self) -> float: ...
    @property
    def backend_timestamp(self) -> DateTime: ...
    @property
    def client_timestamp(self) -> DateTime: ...

class RepAlreadyBootstrapped(Rep):
    def __init__(
        self,
    ) -> None: ...

class RepNotFound(Rep):
    def __init__(
        self,
    ) -> None: ...