# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS
from __future__ import annotations

import importlib.resources
from collections.abc import Callable
from typing import Any

from jinja2 import BaseLoader, Environment, StrictUndefined, Template, TemplateNotFound


class PackageLoader(BaseLoader):
    def __init__(self, path: str) -> None:
        self.path = path

    def get_source(self, environment: Any, template: str) -> tuple[str, str, Callable[[], bool]]:
        from parsec import templates  # Self import \o/

        try:
            source = importlib.resources.files(templates).joinpath(template).read_text()
        except FileNotFoundError as exc:
            raise TemplateNotFound(template) from exc
        return source, self.path, lambda: True


# Env config is also needed to configure the ASGI app
JINJA_ENV_CONFIG = {
    "loader": PackageLoader("parsec.backend.http.templates"),
    "undefined": StrictUndefined,
}
JINJA_ENV = Environment(**JINJA_ENV_CONFIG)


def get_template(name: str | Template) -> Template:
    return JINJA_ENV.get_template(name)
