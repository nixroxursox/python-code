from http import HTTPStatus
from typing import Iterable, Optional
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.requests import Request
from typing import Any, MutableMapping

import structlog

from starlette_context import context


# from .wrappers import Response

# The set of HTTP status errors exposed by Werkzeug by default
WERKZEUG_EXCEPTION_CODES = [
    400,
    401,
    403,
    404,
    405,
    406,
    408,
    409,
    410,
    411,
    412,
    413,
    414,
    415,
    416,
    417,
    422,
    423,
    428,
    429,
    431,
    451,
    500,
    501,
    502,
    503,
    504,
    505,
]


class HTTPException(Exception):
    def __init__(self, status_code: int, description: str, name: str) -> None:
        self.status_code = status_code
        self.description = description
        self.name = name

    def get_body(self) -> str:
        """Get the HTML body."""
        return f"""
<!doctype html>
<title>{self.status_code} {self.name}</title>
<h1>{self.name}</h1>
{self.description}
        """

    def get_response(self) -> Response:
        return Response(
            self.get_body(),
            status=self.status_code,
            headers=self.get_headers(),
        )

    def get_headers(self) -> dict:
        return {"Content-Type": "text/html"}


class HTTPStatusException(HTTPException):
    status = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(self, status: Optional[HTTPStatus] = None) -> None:
        self.status = status or self.status
        super().__init__(self.status.value, self.status.description, self.status.phrase)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.status})"


class BadRequest(HTTPStatusException):
    status = HTTPStatus.BAD_REQUEST


class NotFound(HTTPStatusException):
    status = HTTPStatus.NOT_FOUND


class MethodNotAllowed(HTTPStatusException):
    def __init__(self, allowed_methods: Optional[Iterable[str]] = None) -> None:
        super().__init__(HTTPStatus.METHOD_NOT_ALLOWED)
        self.allowed_methods = allowed_methods

    def get_headers(self) -> dict:
        headers = super().get_headers()
        headers.update({"Allow": ", ".join(self.allowed_methods)})
        return headers


class UnavailableForLegalReasons(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            451,
            "The server is denying access to the resource as a consequence of a legal demand",
            "Unavailable for legal reasons",
        )


class RedirectRequired(HTTPStatusException):
    def __init__(self, redirect_path: str) -> None:
        super().__init__(HTTPStatus.MOVED_PERMANENTLY)
        self.redirect_path = redirect_path

    def get_body(self) -> str:
        return f"""
<!doctype html>
<title>Redirect</title>
<h1>Redirect</h1>
You should be redirected to <a href="{self.redirect_path}">{self.redirect_path}</a>,
it not please click the link
    """

    def get_headers(self) -> dict:
        headers = super().get_headers()
        headers.update({"Location": self.redirect_path})
        return headers


def abort(status_code: int) -> None:
    error_class = all_http_exceptions.get(status_code)
    if error_class is None:
        raise HTTPException(status_code, "Unknown", "Unknown")
    else:
        raise error_class()


all_http_exceptions = {
    status.value: type(
        f"{status.name}Error", (HTTPStatusException,), {"status": status}
    )
    for status in HTTPStatus  # type: ignore
}

default_exceptions = {
    code: all_http_exceptions[code] for code in WERKZEUG_EXCEPTION_CODES if code != 451
}

# Python does not yet have 451, see https://bugs.python.org/issue26589
default_exceptions[451] = UnavailableForLegalReasons


def setup_logging():
    import logging.config

    def add_app_context(
        logger: logging.Logger,
        method_name: str,
        event_dict: MutableMapping[str, Any],
    ) -> MutableMapping[str, Any]:
        if context.exists():
            event_dict.update(context.data)
        return event_dict

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            add_app_context,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.AsyncBoundLogger,
        cache_logger_on_first_use=True,
    )

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
            },
        },
        "handlers": {
            "json": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "json",
            },
        },
        "loggers": {
            "starlette_context_example": {
                "handlers": ["json"],
                "level": "INFO",
            },
            "uvicorn": {"handlers": ["json"], "level": "INFO"},
            "uvicorn.error": {"handlers": ["json"], "level": "INFO"},
            "uvicorn.access": {
                "handlers": ["json"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    logging.config.dictConfig(logging_config)
