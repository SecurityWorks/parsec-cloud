# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

from typing import Any, BinaryIO

import qrcode.image.base

class PilImage(qrcode.image.base.BaseImage):
    def save(self, stream: BinaryIO, **kwargs: Any) -> None: ...