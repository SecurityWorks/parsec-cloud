# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

from parsec._parsec import DateTime, DeviceID

class Message:
    def __init__(
        self, index: int, sender: DeviceID, timestamp: DateTime, body: bytes, certificate_index: int
    ) -> None: ...
    @property
    def index(self) -> int: ...
    @property
    def sender(self) -> DeviceID: ...
    @property
    def timestamp(self) -> DateTime: ...
    @property
    def body(self) -> bytes: ...
    @property
    def certificate_index(self) -> int: ...

class Req:
    def __init__(self, offset: int) -> None: ...
    def dump(self) -> bytes: ...
    @property
    def offset(self) -> int: ...

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
    def __init__(self, messages: list[Message]) -> None: ...
    @property
    def messages(self) -> list[Message]: ...