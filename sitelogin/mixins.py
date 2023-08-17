from starlette.authentication import BaseUser
from user import User


class UserMixin(BaseUser):
    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(nn) -> str:
        uu = User()
        d = uu.find(un)
        dd = d["loginData"]
        nn = d["nickName"]
        return nn

    @property
    def identity(self) -> str:
        raise NotImplementedError()  # pragma: no cover


class AnonymousUser(BaseUser):
    @property
    def is_authenticated(self) -> bool:
        return False

    @property
    def display_name(self) -> str:
        return None

    @property
    def identity(self):
        return
