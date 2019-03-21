from parsec.logging import configure_sentry_logging, disable_sentry_logging, sentry_logging_activated

from parsec.core.gui import settings


def init(config):
    if settings.get_value("global/sentry_logging", "true") and config.sentry_url:
        configure_sentry_logging(config.sentry_url)
    else:
        disable_sentry_logging()
