from starlette.applications import Request, Response, Starlette
from starlette.authentication import requires
from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

template = Jinja2Templates(directory="templates")


class ImproperlyConfigured(Exception):
    
    pass

async def not_found(request: Request, exc: HTTPException):
    """
    Return an HTTP 404 page.
    """
    template = "404.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context, status_code=404)


async def server_error(request: Request, exc: HTTPException):
    """
    Return an HTTP 500 page.
    """
    template = "500.html"
    context = {"request": request}
    return template.TemplateResponse(template, context, status_code=500)
