# Parsec Cloud (https://parsec.cloud) Copyright (c) AGPL-3.0 2016-present Scille SAS

from __future__ import annotations

class ApiVersion:
    API_V1_VERSION: ApiVersion
    API_V2_VERSION: ApiVersion
    API_VERSION: ApiVersion

    def __init__(self, version: int, revision: int) -> None: ...
    def dump(self) -> bytes: ...
    @classmethod
    def from_str(cls, version_str: str) -> ApiVersion: ...
    @classmethod
    def from_bytes(cls, bytes: bytes) -> ApiVersion: ...
    @property
    def version(self) -> int: ...
    @property
    def revision(self) -> int: ...
    def __lt__(self, other: ApiVersion) -> bool: ...
    def __le__(self, other: ApiVersion) -> bool: ...
    def __gt__(self, other: ApiVersion) -> bool: ...
    def __ge__(self, other: ApiVersion) -> bool: ...
