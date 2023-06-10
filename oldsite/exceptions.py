def test_main():
    assert main() is None
import jinja2
from jinja2 import exceptions, environment


# @app.errorhandler(404)
async def not_found(request, exc):
    """
    Return an HTTP 404 page.
    """
    template = "404.html"
    context = {"request": request}
    return ssa.TemplateResponse(template, context, status_code=404)

# @app.errorhandler(500)
async def server_error(request, exc):
    """
    Return an HTTP 500 page.
    """
    template = "500.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context, status_code=500)

# @app.errorhandler(401)
async def unprocessable(request, exc):
    """
    Return an HTTP 401 page.
    """
    template = "401.html"
    context = {"request": request}
    content={"Error": "Invalid request"}
    return templates.TemplateResponse(template, context, content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

