from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()

bcrypt = Bcrypt()


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)


class User(db.Model):
    """Site user."""

    __tablename__ = "users"

    username = db.Column(db.String(20),
                         primary_key=True,
                         )

    password = db.Column(db.String(100),
                         nullable=False
                         )

    email = db.Column(db.String(50),
                         nullable=False,
                         unique=True
                         )

    first_name = db.Column(db.String(30),
                         nullable=False,
                         )
    last_name = db.Column(db.String(30),
                         nullable=False,
                         )

    notes = db.relationship('Note', backref='user')

    @classmethod
    def register(cls, username, password, email, first_name, last_name):
        """ Creates a new a new user instance and returns it. """
        hash = bcrypt.generate_password_hash(password).decode('utf8')

        return cls(
                    username=username, 
                    password=hash, 
                    email=email,
                    first_name=first_name,
                    last_name=last_name
                )

    @classmethod
    def authenticate(cls, username, password):
        """ Creates a new a new user instance and returns it. """
        user = cls.query.filter_by(username=username).one_or_none()
        
        if user and bcrypt.check_password_hash(user.password, password):
            return user
        
        return False

class Note(db.Model):
    """ Creates a note"""
    __tablename__ = 'notes'

    id = db.Column(db.Integer,
                    primary_key=True,
                    autoincrement=True
                    )

    title = db.Column(db.String(100),
                         nullable=False
                         )

    content = db.Column(db.Text,
                         nullable=False
                         )
    
    owner = db.Column(db.String(20),
                         db.ForeignKey('users.username'),
                         nullable=False
                         )