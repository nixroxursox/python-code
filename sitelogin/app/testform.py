from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
from starlette_wtf import StarletteForm, CSRFProtectMiddleware, csrf_protect
from wtforms import PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms.widgets import PasswordInput

templates = Jinja2Templates(directory="templates")


class testform(StarletteForm):
    """Create account form
    """
    email = TextAreaField(
        'Email address',
        validators=[
            DataRequired('Please enter your email address'),
            Email()
        ]
    )

    password = PasswordField(
        'Password',
        widget=PasswordInput(hide_value=False),
        validators=[
            DataRequired('Please enter your password'),
            EqualTo('password_confirm', message='Passwords must match')
        ]
    )

    password_confirm = PasswordField(
        'Confirm Password',
        widget=PasswordInput(hide_value=False),
        validators=[
            DataRequired('Please confirm your password')
        ]
    )


@csrf_protect
async def fregister(request):
    """GET|POST /create-account: create account form handler
    """
    # initialize form
    form = await testform.from_formdata(request)

    # validate form
    if form.validate_on_submit():
        # TODO: Save account credentials before returning redirect response
        return RedirectResponse(url='/profile', status_code=303)

    # return form html
    context = {'request': request, 'form': form}
    status_code = 422 if form.errors else 200

    return templates.TemplateResponse('/testform.html',
                                      context=context,
                                      status_code=status_code)
