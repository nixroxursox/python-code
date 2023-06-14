# async def app(scope, receive, send):
#     if scope["type"] != "http":
#         raise Exception("Only the HTTP protocol is supported")

#     await send({
#         'type': 'http.response.start',
#         'status': 200,
#         'headers': [
#             (b'content-type', b'text/plain'),
#             (b'content-length', b'5'),
#         ],
#     })
#     await send({
#         'type': 'http.response.body',
#         'body': b'hello',
#     })

from quart import Quart

app = Quart(__name__)

@app.route("/hello")
async def hello():
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True)

