# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

from parsec._parsec import DateTime, EnrollmentID

class PkiEnrollmentInfoStatus:
    pass

class PkiEnrollmentInfoStatusSubmitted(PkiEnrollmentInfoStatus):
    def __init__(self, submitted_on: DateTime) -> None: ...
    @property
    def submitted_on(self) -> DateTime: ...

class PkiEnrollmentInfoStatusAccepted(PkiEnrollmentInfoStatus):
    def __init__(
        self,
        submitted_on: DateTime,
        accepted_on: DateTime,
        accepter_der_x509_certificate: bytes,
        accept_payload_signature: bytes,
        accept_payload: bytes,
    ) -> None: ...
    @property
    def submitted_on(self) -> DateTime: ...
    @property
    def accepted_on(self) -> DateTime: ...
    @property
    def accepter_der_x509_certificate(self) -> bytes: ...
    @property
    def accept_payload_signature(self) -> bytes: ...
    @property
    def accept_payload(self) -> bytes: ...

class PkiEnrollmentInfoStatusRejected(PkiEnrollmentInfoStatus):
    def __init__(self, submitted_on: DateTime, rejected_on: DateTime) -> None: ...
    @property
    def submitted_on(self) -> DateTime: ...
    @property
    def rejected_on(self) -> DateTime: ...

class PkiEnrollmentInfoStatusCancelled(PkiEnrollmentInfoStatus):
    def __init__(self, submitted_on: DateTime, cancelled_on: DateTime) -> None: ...
    @property
    def submitted_on(self) -> DateTime: ...
    @property
    def cancelled_on(self) -> DateTime: ...

class Req:
    def __init__(self, enrollment_id: EnrollmentID) -> None: ...
    def dump(self) -> bytes: ...
    @property
    def enrollment_id(self) -> EnrollmentID: ...

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
    def __init__(self, unit: PkiEnrollmentInfoStatus) -> None: ...
    @property
    def unit(self) -> PkiEnrollmentInfoStatus: ...

class RepNotFound(Rep):
    def __init__(self, reason: str | None) -> None: ...
    @property
    def reason(self) -> str | None: ...