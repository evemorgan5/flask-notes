"""flask app that stores passwords hashed with Bcrypt. Yay!"""

from flask import Flask, render_template, redirect, session
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Note
from forms import AddNoteForm, RegisterForm, LoginForm, CSRFProtectForm

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
    """ If logged in, displayer user page. If not redirects to homepage."""
    if not session.get(SESSION_KEY) == username:
        return redirect("/")

    user = User.query.get_or_404(username)
    form = CSRFProtectForm()
    return render_template("user.html", user=user, form=form)

@app.post("/logout")
def logout():
    """Checks if logged in, logs user out and redirects to homepage.
     Else redirects to homepage."""
    if SESSION_KEY not in session:
        return redirect("/")

    form = CSRFProtectForm()

    if form.validate_on_submit():
        # Remove username if present, but no errors if it wasn't
        session.pop(SESSION_KEY, None)

    return redirect("/")

@app.post('/users/<username>/delete')
def delete_user(username):
    """ If logged in, if theres a user with that username, deletes all of
    its notes, deletes the user, and clears the session. Then redirects to
    homepage.
    If no user with that username exists, give a 404. """
    if not session.get(SESSION_KEY) == username:
        return redirect("/")

    form = CSRFProtectForm()

    if form.validate_on_submit():
        user = User.query.get_or_404(username)
        notes = user.notes

        for note in notes:
            db.session.delete(note)

        db.session.delete(user)
        db.session.commit()
        session.pop(SESSION_KEY, None)

    return redirect('/')

@app.route("/users/<username>/notes/add", methods=["GET", "POST"])
def add_notes(username):
    """ POST: If logged in, get note information from form add to database
    and redirect to users user page.
    GET: If logged in, render template for addnotes to that user."""
    if not session.get(SESSION_KEY) == username:
        return redirect("/")

    form = AddNoteForm()
    user = User.query.get_or_404(username)

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        note = Note(owner=username, title=title, content=content)
        db.session.add(note)
        db.session.commit()

        return redirect(f"/users/{username}")

    else:
        return render_template("addnotes.html", user=user, form=form)


@app.route("/notes/<int:note_id>/update", methods=["GET", "POST"])
def edit_note(note_id):
    """ POST: If logged in, grab data from form to update note in database
    and redirect to users user page.
    GET: If logged in, render template for editnotes for the user."""
    if not session.get(SESSION_KEY) == username:
        return redirect("/")

    note = Note.query.get_or_404(note_id)
    form = AddNoteForm(title=note.title, content=note.content)
    user = note.user

    if form.validate_on_submit():
        note.title = form.title.data
        note.content = form.content.data

        db.session.commit()
        return redirect(f"/users/{user.username}")

    else:
        return render_template("editnotes.html", note=note, form=form)


@app.post("/notes/<int:note_id>/delete")
def delete_note(note_id):
    """ If logged in, delete note for user and redirect to users user page."""
    if not session.get(SESSION_KEY) == username:
        return redirect("/")
    note = Note.query.get_or_404(note_id)
    user = note.user

    form = CSRFProtectForm()

    if form.validate_on_submit():
        db.session.delete(note)
        db.session.commit()

    return redirect(f"/users/{user.username}")