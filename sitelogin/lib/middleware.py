from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware


middleware = [
    Middleware(
        TrustedHostMiddleware,
        allowed_hosts=['onion.com', '*.onion.com'],
    ),
    Middleware(HTTPSRedirectMiddleware)
]