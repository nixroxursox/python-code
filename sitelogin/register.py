from decouple import config
from quart import Quart, request, session, render_template, redirect, url_for
import re
from db.dB import dataBase, queries
import user
import app


# Make function for logout session
@app.route("/logout")
async def logout():
    session.pop("loggedin", None)
    session.pop("userid", None)
    session.pop("email", None)
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
async def register():
    message = ""
    userDict = {
        "fnickName": "request.form['NickName']",
        "fpassword": "request.form['password']",
        "fpinCode": "request.form['pinCode']",
        "fuserId": "request.form['userId']",
    }


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
#     message = ""
#     if request.method == "POST":
#         dbr = dataBase.Config("write")
#         rcol = dbr["luser"]
#         session["loggedin"] = True
#         session["userId"] = user["userid"]
#         session["NickName"] = user["NickName"]
#         session["pinCode"] = user["userId"]
#         message = "Registered successfully !"
#         return await render_template("auth/login.html", message=message)
#     else:
#         message = "Please enter correct email / password !"
#         return render_template("login.html", message=message)


# Make a register session for registration session
# and also connect to Mysql to code for access login
# and for completing our login
# session and making some flashing massage for error

# dbw = dataBase.Config("write")
# rcol = dbw["luser"]
# rcol.insert_one({}, queries.insert_one())
# 	## g(userId, NickName, password, pinCode ))
# message = 'You have successfully registered !'
# elif request.method == 'POST':
# 	message = 'Please fill out the form !'
# return render_template('register.html', message=message)
