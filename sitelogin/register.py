from decouple import config
from db.dB import dataBase
from user import User
import time
from starlette.applications import Starlette, Request, Response, ASGIApp
from starlette.responses import JSONResponse
from starlette.routing import Route
from main import app

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


@app.route("/register", methods=["GET", "POST"])
async def register():
    message = "Checking for registration..."
    if request.method == "POST":
        wdb = dataBase.Config("write")
        db = wdb["luser"]
        rsess = {}
        rsess["userId"] = user["userid"]
        rsess["password"] = user["password"]
        rsess["NickName"] = user["NickName"]
        rsess["pinCode"] = user["pinCode"]
        regDate = time.strftime("%Y.%m.%d:%H:%M:%S")
        rsess["regDate"] = regDate
        message = "Registered successfully !"
        return await render_template("auth/login.html", message=message)
    else:
        message = "Please enter correct email / password !"
        return render_template("register.html", message=message)


# Make a register rsess for registration rsess
# and also connect to Mysql to code for access login
# and for completing our login
# rsess and making some flashing massage for error

# wdb = dataBase.Config("write")
# db = wdb["luser"]
# db.insert_one({},
# g(userId, NickName, password, pinCode ))
# message = 'You have successfully registered !'
# elif request.method == 'POST':
# 	message = 'Please fill out the form !'
# return render_template('register.html', message=message)
