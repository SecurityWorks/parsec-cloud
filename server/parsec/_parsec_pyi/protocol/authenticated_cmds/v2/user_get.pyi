# Parsec Cloud (https://parsec.cloud) Copyright (c) AGPL-3.0 2016-present Scille SAS

from __future__ import annotations

from parsec._parsec import UserID

class Trustchain:
    def __init__(
        self, devices: list[bytes], users: list[bytes], revoked_users: list[bytes]
    ) -> None: ...
    @property
    def devices(self) -> list[bytes]: ...
    @property
    def users(self) -> list[bytes]: ...
    @property
    def revoked_users(self) -> list[bytes]: ...

class Req:
    def __init__(self, user_id: UserID) -> None: ...
    def dump(self) -> bytes: ...
    @property
    def user_id(self) -> UserID: ...

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
        user_certificate: bytes,
        revoked_user_certificate: bytes | None,
        device_certificates: list[bytes],
        trustchain: Trustchain,
    ) -> None: ...
    @property
    def user_certificate(self) -> bytes: ...
    @property
    def revoked_user_certificate(self) -> bytes | None: ...
    @property
    def device_certificates(self) -> list[bytes]: ...
    @property
    def trustchain(self) -> Trustchain: ...

class RepNotFound(Rep):
    def __init__(
        self,
    ) -> None: ...
