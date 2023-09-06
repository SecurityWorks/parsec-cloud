# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

from triopg._triopg import connect, create_pool

__all__ = ("connect", "create_pool")

class UniqueViolationError(Exception): ...
class UndefinedTableError(Exception): ...

class PostgresError(Exception):
    @property
    def message(self) -> str: ...