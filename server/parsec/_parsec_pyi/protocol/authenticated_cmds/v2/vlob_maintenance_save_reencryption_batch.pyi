# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

from parsec._parsec import RealmID, ReencryptionBatchEntry

class Req:
    def __init__(
        self, realm_id: RealmID, encryption_revision: int, batch: list[ReencryptionBatchEntry]
    ) -> None: ...
    def dump(self) -> bytes: ...
    @property
    def realm_id(self) -> RealmID: ...
    @property
    def encryption_revision(self) -> int: ...
    @property
    def batch(self) -> list[ReencryptionBatchEntry]: ...

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
    def __init__(self, total: int, done: int) -> None: ...
    @property
    def total(self) -> int: ...
    @property
    def done(self) -> int: ...

class RepNotAllowed(Rep):
    def __init__(
        self,
    ) -> None: ...

class RepNotFound(Rep):
    def __init__(self, reason: str | None) -> None: ...
    @property
    def reason(self) -> str | None: ...

class RepNotInMaintenance(Rep):
    def __init__(self, reason: str | None) -> None: ...
    @property
    def reason(self) -> str | None: ...

class RepBadEncryptionRevision(Rep):
    def __init__(
        self,
    ) -> None: ...

class RepMaintenanceError(Rep):
    def __init__(self, reason: str | None) -> None: ...
    @property
    def reason(self) -> str | None: ...