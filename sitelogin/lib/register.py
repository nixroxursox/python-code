import time
from urllib.parse import parse_qsl, urlparse

from decouple import config
from starlette.applications import ASGIApp, Request, Response, Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from db.dB import dataBase
from main import app
from user import User

request = Request
response = Response


# Make function for logout rsess
@app.route("/logout")
async def logout():
    rsess = {}
    rsess.pop("loggedin", None)
    rsess.pop("userid", None)
    rsess.pop("email", None)
    return redirect(url_for("login"))


# @app.route("/register", methods=["GET", "POST"])
# async def register():
#     message = ""
#     userDict = {
#         "fnickName": "request.form['NickName']",
#         "fpassword": "request.form['password']",
#         "fpinCode": "request.form['pinCode']",
#         "fuserId": "request.form['userId']",
#     }


# Add data to MongoDB route
@app.route("/add_data", methods=["POST"])
async def add_data():
    # ftyGet data from request
    data = request.json

    # Insert data into MongoDB
    collection.insert_one(data)

    return "Data added to MongoDB"


# @app.route("/register", methods=["GET", "POST"])
# async def register():
#     message = "Checking for registration..."
#     if request.method == "POST":
#         wdb = dataBase.Config("write")
#         db = wdb["userData"]
#         body = (await request.body()).decode()
#         user = dict(parse_qsl(body))
#         un = user["userid"]
#         pw = user["password"]
#         nn = user["NickName"]
#         pi = user["pinCode"]
#         rd = time.strftime("%Y.%m.%d:%H:%M:%S")
#         user["regDate"] = rd
#         uu = User()
#         uu.create(un, pw, pin, nn)
#         message = "Registered successfully !"
#         return await render_template("auth/login.html", message=message)
#     else:
#         message = "Please enter correct email / password !"
#         return render_template("register.html", message=message)


# # Make a register rsess for registration rsess
# # and also connect to Mysql to code for access login
# and for completing our login
# rsess and making some flashing massage for error

# wdb = dataBase.Config("write")
# db = wdb["userData"]
# db.insert_one({},
# g(userId, NickName, password, pinCode ))
# message = 'You have successfully registered !'
# elif request.method == 'POST':
# 	message = 'Please fill out the form !'
# return render_template('register.html', message=message)
