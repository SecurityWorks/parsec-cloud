# Parsec Cloud (https://parsec.cloud) Copyright (c) AGPL-3.0 2016-present Scille SAS

from __future__ import annotations

from typing import Iterable

from ..ids import ShamirRevealToken

class ShamirRecoveryOthersListReq:
    def __init__(self) -> None: ...
    def dump(self) -> bytes: ...

class ShamirRecoveryOthersListRep:
    def dump(self) -> bytes: ...
    @classmethod
    def load(cls, buf: bytes) -> ShamirRecoveryOthersListRep: ...

class ShamirRecoveryOthersListRepOk(ShamirRecoveryOthersListRep):
    def __init__(
        self, brief_certificates: Iterable[bytes], share_certificates: Iterable[bytes]
    ) -> None: ...
    @property
    def brief_certificates(self) -> tuple[bytes, ...]: ...
    @property
    def share_certificates(self) -> tuple[bytes, ...]: ...

class ShamirRecoveryOthersListRepNotAllowed(ShamirRecoveryOthersListRep): ...

class ShamirRecoveryOthersListRepUnknownStatus(ShamirRecoveryOthersListRep):
    def __init__(self, status: str, reason: str | None) -> None: ...
    @property
    def status(self) -> str: ...
    @property
    def reason(self) -> str | None: ...

class ShamirRecoverySelfInfoReq:
    def __init__(self) -> None: ...
    def dump(self) -> bytes: ...

class ShamirRecoverySelfInfoRep:
    def dump(self) -> bytes: ...
    @classmethod
    def load(cls, buf: bytes) -> ShamirRecoverySelfInfoRep: ...

class ShamirRecoverySelfInfoRepOk(ShamirRecoverySelfInfoRep):
    def __init__(self, self_info: bytes | None) -> None: ...
    @property
    def self_info(self) -> bytes | None: ...

class ShamirRecoverySelfInfoRepUnknownStatus(ShamirRecoverySelfInfoRep):
    def __init__(self, status: str, reason: str | None) -> None: ...
    @property
    def status(self) -> str: ...
    @property
    def reason(self) -> str | None: ...

class ShamirRecoverySetup:
    def __init__(
        self,
        ciphered_data: bytes,
        reveal_token: ShamirRevealToken,
        brief: bytes,
        shares: Iterable[bytes],
    ) -> None: ...
    @property
    def ciphered_data(self) -> bytes: ...
    @property
    def reveal_token(self) -> ShamirRevealToken: ...
    @property
    def brief(self) -> bytes: ...
    @property
    def shares(self) -> tuple[bytes, ...]: ...

class ShamirRecoverySetupReq:
    def __init__(self, setup: ShamirRecoverySetup | None) -> None: ...
    def dump(self) -> bytes: ...
    @property
    def setup(self) -> ShamirRecoverySetup | None: ...

class ShamirRecoverySetupRep:
    def dump(self) -> bytes: ...
    @classmethod
    def load(cls, buf: bytes) -> ShamirRecoverySetupRep: ...

class ShamirRecoverySetupRepOk(ShamirRecoverySetupRep):
    def __init__(self) -> None: ...

class ShamirRecoverySetupRepInvalidCertification(ShamirRecoverySetupRep): ...
class ShamirRecoverySetupRepInvalidData(ShamirRecoverySetupRep): ...
class ShamirRecoverySetupRepAlreadySet(ShamirRecoverySetupRep): ...

class ShamirRecoverySetupRepUnknownStatus(ShamirRecoverySetupRep):
    def __init__(self, status: str, reason: str | None) -> None: ...
    @property
    def status(self) -> str: ...
    @property
    def reason(self) -> str | None: ...

class InviteShamirRecoveryRevealReq:
    def __init__(self, reveal_token: ShamirRevealToken) -> None: ...
    def dump(self) -> bytes: ...
    @property
    def reveal_token(self) -> ShamirRevealToken: ...

class InviteShamirRecoveryRevealRep:
    def dump(self) -> bytes: ...
    @classmethod
    def load(cls, buf: bytes) -> InviteShamirRecoveryRevealRep: ...

class InviteShamirRecoveryRevealRepOk(InviteShamirRecoveryRevealRep):
    def __init__(self, ciphered_data: bytes) -> None: ...
    @property
    def ciphered_data(self) -> bytes: ...

class InviteShamirRecoveryRevealRepNotFound(InviteShamirRecoveryRevealRep): ...

class InviteShamirRecoveryRevealRepUnknownStatus(InviteShamirRecoveryRevealRep):
    def __init__(self, status: str, reason: str | None) -> None: ...
    @property
    def status(self) -> str: ...
    @property
    def reason(self) -> str | None: ...