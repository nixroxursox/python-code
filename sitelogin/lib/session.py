from decouple import config

# from redis import Redis
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette_session import SessionMiddleware
from starlette_session.backends import BackendType

sk = config("SESS_SECRET_KEY")


async def setup_session(request: Request) -> JSONResponse:
    request.session.update({"data": "session_data"})
    return JSONResponse({"session": request.session})


async def clear_session(request: Request):
    request.session.clear()
    return JSONResponse({"session": request.session})


def view_session(request: Request) -> JSONResponse:
    return JSONResponse({"session": request.session})


# redis_client = Redis(host="localhost", port=6379)
# # app = Starlette(debug=True, routes=routes)
# # app.add_middleware(
# #     SessionMiddleware,
# #     secret_key=sk,
# #     cookie_name="cookie22",
# #     backend_type=redis
# #     backend_clientredis__client,
# # )
