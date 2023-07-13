from flask import Flask, render_template, flash, request, url_for, redirect, session
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
import gc


@app.route("/login/", methods=["GET", "POST"])
def login_page():
    error = ""
    try:
        c, conn = connection()
        if request.method == "POST":
            data = c.execute(
                "SELECT * FROM users WHERE username = (%s)",
                thwart(request.form["username"]),
            )

            data = c.fetchone()[2]

            if sha256_crypt.verify(request.form["password"], data):
                session["logged_in"] = True
                session["username"] = request.form["username"]

                flash("You are now logged in")
                return redirect(url_for("dashboard"))

            else:
                error = "Invalid credentials, try again."

        gc.collect()

        return render_template("login.html", error=error)

    except Exception as e:
        # flash(e)
        error = "Invalid credentials, try again."
        return render_template("login.html", error=error)


@app.route("/register/", methods=["GET", "POST"])
def register_page():
    try:
        form = RegistrationForm(request.form)

        if request.method == "POST" and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data)))
            c, conn = connection()

            x = c.execute(
                "SELECT * FROM users WHERE username = (%s)", (thwart(username))
            )

            if int(x) > 0:
                flash("That username is already taken, please choose another")
                return render_template("register.html", form=form)

            else:
                c.execute(
                    "INSERT INTO users (username, password, email, tracking) VALUES (%s, %s, %s, %s)",
                    (
                        thwart(username),
                        thwart(password),
                        thwart(email),
                        thwart("/introduction-to-python-programming/"),
                    ),
                )

                conn.commit()
                flash("Thanks for registering!")
                c.close()
                conn.close()
                gc.collect()

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("dashboard"))

        return render_template("register.html", form=form)

    except Exception as e:
        return str(e)
