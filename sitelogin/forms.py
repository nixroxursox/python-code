
from starlette.requests import Request
from wtforms import fields, form, validators, StringField, IntegerField, PasswordField
from starlette.templating import Jinja2Templates
from starsessions.exceptions import ImproperlyConfigured
from user import User
from starlette.exceptions import HTTPException
from nacl.encoding import URLSafeBase64Encoder

template = Jinja2Templates(directory="templates")
templates = Jinja2Templates(directory="templates")

b64_encode = URLSafeBase64Encoder.encode
b64_decode = URLSafeBase64Encoder.decode


class ChangePasswordForm(form.Form):
    current_password = fields.PasswordField(validators=[validators.DataRequired()])
    new_password = fields.PasswordField(validators=[validators.DataRequired()])
    confirm_new_password = fields.PasswordField(
        validators=[
            validators.DataRequired(),
            validators.EqualTo("new_password", message="The passwords do not match."),
        ]
    )


class LoginForm(form.Form):
    strf = StringField
    userId = strf(
        validators=[
            validators.DataRequired()
        ]
    )
    password = fields.PasswordField(validators=[validators.DataRequired()])


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
    #msg = message_logger.send_message

    #     if (
    #         not config.reset_pw_email_subject_template
    #         or not config.reset_pw_email_template
    #     ):
    def error_message():
        msg =     (
                "To sent a password reset email you must specify both the "
                "`reset_pw_email_subject_template` and `reset_pw_email_template` "
                "templates. Additionally you can also specify the "
                "`reset_pw_html_email_template` to send an html version."
            )
        #raise ImproperlyConfigured(error_message)

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
