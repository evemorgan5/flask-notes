"""flask app that stores passwords hashed with Bcrypt. Yay!"""

from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User
from forms import RegisterForm, LoginForm, CSRFProtectForm

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///notes"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)

SESSION_KEY = 'username'

@app.get("/")
def homepage_redirect():
    """ Redirects to register page """
    return redirect("/register")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user: produce form & handle form submission."""

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(
                        username, 
                        password, 
                        email, 
                        first_name, 
                        last_name
                    )
        db.session.add(user)
        db.session.commit()

        session[SESSION_KEY] = user.username

        # on successful login, redirect to secret page
        return redirect(f"/users/{username}")

    else:
        return render_template("register.html", form=form)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Produce login form or handle login."""

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # authenticate will return a user or False
        user = User.authenticate(username, password)

        if user:
            session[SESSION_KEY] = user.username  # keep logged in
            return redirect(f"/users/{username}")

        else:
            form.username.errors = ["Bad name/password"]

    return render_template("login.html", form=form)


@app.get("/users/<username>")
def display_user(username):
    """ If logged in, displayer user page. If not redirects to login page. """
    user = User.query.get_or_404(username)
    form = CSRFProtectForm()

    if SESSION_KEY not in session:
        return redirect("/login")
    else:
        return render_template("user.html", user=user, form=form)


@app.post("/logout")
def logout():
    """Logs user out and redirects to homepage."""

    form = CSRFProtectForm()

    if form.validate_on_submit():
        # Remove username if present, but no errors if it wasn't
        session.pop(SESSION_KEY, None)

    return redirect("/")

@app.post('/users/<username>/delete')
def delete_user(username):
    """ If theres a user with that username, deletes all of its notes,
        deletes the user, and clears the session. Then redirects to 
        homepage. 
        If no user with that username exists, give a 404. """
    user = User.query.get_or_404(username)
    notes = user.notes

    for note in notes:
        db.session.delete(note)

    db.session.delete(user)
    db.session.commit()

    session.pop(SESSION_KEY, None)

    return redirect('/')



