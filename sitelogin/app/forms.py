from starlette.requests import Request, HTTPConnection
from wtforms import (
    fields,
    form,
    validators,
    StringField,
    IntegerField,
    PasswordField,
    SubmitField,
    TextAreaField
)
import jinja2
from jinja2 import Environment, FileSystemLoader
from starlette.requests import Request, HTTPConnection
from starlette.templating import Request as StarletteRequest, Jinja2Templates
from wtforms.widgets import PasswordInput
from wtforms.validators import DataRequired, DataRequired, Length
from starlette.exceptions import HTTPException
from nacl.encoding import URLSafeBase64Encoder
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import RedirectResponse, JSONResponse, Response, HTMLResponse
from starlette_wtf import StarletteForm, CSRFProtectMiddleware, csrf_protect
from wtforms.validators import DataRequired, Email, EqualTo
from user import User


b64_encoder = URLSafeBase64Encoder.encode
b64_decoder = URLSafeBase64Encoder.decode
env = Environment(loader=FileSystemLoader("templates"))
templates = Jinja2Templates(env=env)
request = Request
response = Response


class ChangePasswordForm(form.Form):
    current_password = fields.PasswordField(validators=[validators.DataRequired()])
    new_password = fields.PasswordField(validators=[validators.DataRequired()])
    confirm_new_password = fields.PasswordField(validators=[validators.DataRequired()])


class LoginForm(StarletteForm):
    username = fields.StringField(
        name="username",
        id="username",
        validators=[
            DataRequired(),
            Length(min=10, max=50,
                   message="Must be between ten and fifty Characters"),
        ],
    )
    nickName = fields.StringField(
        name="nickName",
        id="nickName",
        validators=[
            DataRequired(),
            Length(min=10, max=50,
                   message="Must be between ten and fifty Characters"),
        ],
    )
    password = fields.PasswordField(
        name="password",
        id="password",
        validators=[
            DataRequired(),
            Length(min=8, max=35,
                   message="must be between 8 and 35 characters"),
        ],
    )
    pinCode = fields.IntegerField(
        validators=[
            DataRequired()
        ]
    )
    submit = SubmitField("submit")


class PasswordResetForm(form.Form):
    # email = EmailField(
    #     validators=[
    #         validators.DataRequired(),
    #         validators.Email(message="Must be a valid email."),
    #     ]
    # )

    # # async def send_email(self, request: Request):
    # #     from . import config

    # #     user = User.query.filter(User.email == self.data["email"]).one_or_none()

    # #     if not user:
    # #         return

    #     templates = config.templates
    #     context = {
    #         "request": request,
    #         "uid": urlsafe_base64_encode(bytes(str(user.id), encoding="utf-8")),
    #         "user": user,
    #         "token": token_generator.make_token(user),
    #     }
    # msg = message_logger.send_message

    #     if (
    #         not config.reset_pw_email_subject_template
    #         or not config.reset_pw_email_template
    #     ):
    def error_message():
        msg = (
            "To sent a password reset email you must specify both the "
            "`reset_pw_email_subject_template` and `reset_pw_email_template` "
            "templates. Additionally you can also specify the "
            "`reset_pw_html_email_template` to send an html version."
        )
        # raise ImproperlyConfigured(error_message)

        # subject_tmpl = templates.get_template(config.reset_pw_email_subject_template)
        # subject = subject_tmpl.render(context)
        # body_tmpl = templates.get_template(config.reset_pw_email_template)
        # body = body_tmpl.render(context)

        # msg["To"] = [user.email]
        # msg["Subject"] = subject
        # msg.set_content(body)

        # if config.reset_pw_html_email_template:
        #     html_body_tmpl = templates.get_template(config.reset_pw_html_email_template)
        #     html_body = html_body_tmpl.render(context)
        #     msg.add_alternative(html_body, subtype="html")

        # send_message(msg)


class PasswordResetConfirmForm(form.Form):
    new_password = fields.PasswordField(validators=[validators.DataRequired()])
    confirm_new_password = fields.PasswordField(
        validators=[
            validators.DataRequired(),
            validators.EqualTo("new_password", message="The passwords do not match."),
        ]
    )


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
    return templates.TemplateResponse(template, context, status_code=500)


class Register(StarletteForm):
    
    """registration form
    """
        
    username = TextAreaField(
        'username',
        validators=[
            DataRequired('Please enter a unique userId'),
        ]
    )

    nickName = TextAreaField(
        'nickName',
        validators=[
            DataRequired('Please enter a Display Name'),
        ]
    )

    password = PasswordField(
        'password',
        widget=PasswordInput(hide_value=False),
        validators=[
            DataRequired('Please enter your password')
        ]
    )

    pinCode = PasswordField(
        'pinCode',
        widget=PasswordInput(hide_value=False),
        validators=[
            DataRequired('Please enter a PIN Code')
        ]
    )
    SubmitField = SubmitField(
        label = 'submit'
    )


class Index(StarletteForm):
    name = StringField('name', validators=[DataRequired()])
    