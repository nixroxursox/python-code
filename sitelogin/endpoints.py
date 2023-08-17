from datetime import datetime

from starlette import status
from starlette.authentication import requires
from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette.responses import RedirectResponse

from config import AppConfig as Config
from config import config
from forms import (
    ChangePasswordForm,
    LoginForm,
    PasswordResetConfirmForm,
    PasswordResetForm,
)
from user import User
from nacl.encoding import URLSafeBase64Encoder
from jinja2 import Environment, FileSystemLoader
from starlette.templating import Jinja2Templates


#template = Jinja2Templates(directory="templates")

class ChangePassword(HTTPEndpoint):
    @requires(["authenticated"])
    async def get(self, request):
        template = config.change_pw_template

        form = ChangePasswordForm()
        context = {"request": request, "form": form}
        return config.templates.TemplateResponse(template, context)

    @requires(["authenticated"])
    async def post(self, request):
        template = config.change_pw_template

        data = await request.form()
        form = ChangePasswordForm(data)

        if not form.validate():
            context = {"request": request, "form": form}
            return config.templates.TemplateResponse(template, context)

        if not request.user.check_password(form.current_password.data):
            form.current_password.errors.append("Enter your current password.")
            context = {"request": request, "form": form}
            return config.templates.TemplateResponse(template, context)

        else:
            request.user.set_password(form.new_password.data)
            request.user.save()

        return RedirectResponse(
            url=config.change_pw_redirect_url, status_code=status.HTTP_302_FOUND
        )


class Login(HTTPEndpoint):
    async def get(self, request):
        template = config.login_template

        form = LoginForm()
        context = {"request": request, "form": form}
        return config.template.TemplateResponse(template, context)

    async def post(self, request):
        template = config.login_template

        data = await request.form()
        form = LoginForm(data)

        if not form.validate():
            context = {"request": request, "form": form}
            return config.templates.TemplateResponse(template, context)

        try:
            user = User.query.filter(User.email == form.email.data.lower()).one()
            if user.check_password(form.password.data):
                request.session["user"] = str(user.id)
                user.last_login = datetime.utcnow()
                user.save()
                return RedirectResponse(
                    url=config.login_redirect_url, status_code=status.HTTP_302_FOUND
                )

        except NoResultFound:
            pass

        request.session.clear()

        form.password.errors.append("userId or password.")
        context = {"request": request, "form": form}

        return config.templates.TemplateResponse(template, context)


class Logout(HTTPEndpoint):
    async def get(self, request):
        request.session.clear()
        return RedirectResponse(
            url=config.logout_redirect_url, status_code=status.HTTP_302_FOUND
        )


class PasswordReset(HTTPEndpoint):
    async def get(self, request):
        template = config.reset_pw_template

        form = PasswordResetForm()
        context = {"request": request, "form": form}
        return config.templates.TemplateResponse(template, context)

    async def post(self, request):
        template = config.reset_pw_template

        data = await request.form()
        form = PasswordResetForm(data)

        if not form.validate():
            context = {"request": request, "form": form}
            return config.templates.TemplateResponse(template, context)

        user = User.query.filter(User.email == form.email.data).one_or_none()
        if user and user.is_active:
            await form.send_email(request)

        return RedirectResponse(
            request.url_for("auth:password_reset_done"),
            status_code=status.HTTP_302_FOUND,
        )


class PasswordResetDone(HTTPEndpoint):
    async def get(self, request):
        template = config.reset_pw_done_template

        context = {"request": request}
        return config.templates.TemplateResponse(template, context)


class PasswordResetConfirm(HTTPEndpoint):
    def get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.query.get(uid)
        except:
            user = None
        return user

    def check_token(self, user, uidb64, token) -> bool:
        if not (user and user.is_active):
            return False
        return bool(token_generator.check_token(user, token))

    async def get(self, request):
        template = config.reset_pw_confirm_template

        uidb64 = request.path_params["uidb64"]
        token = request.path_params["token"]

        user = self.get_user(uidb64)

        if not self.check_token(user, uidb64, token):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        form = PasswordResetConfirmForm()
        context = {"request": request, "form": form}
        return config.templates.TemplateResponse(template, context)

    async def post(self, request):
        template = config.reset_pw_confirm_template

        uidb64 = request.path_params["uidb64"]
        token = request.path_params["token"]

        user = self.get_user(uidb64)

        if not self.check_token(user, uidb64, token):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

        data = await request.form()
        form = PasswordResetConfirmForm(data)

        if not form.validate():
            context = {"request": request, "form": form}
            return config.templates.TemplateResponse(template, context)

        user.set_password(form.new_password.data)
        user.save()

        return RedirectResponse(
            url=request.url_for("auth:password_reset_complete"),
            status_code=status.HTTP_302_FOUND,
        )


class PasswordResetComplete(HTTPEndpoint):
    async def get(self, request):
        template = config.reset_pw_complete_template

        context = {"request": request}
        return config.templates.TemplateResponse(template, context)
