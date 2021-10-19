from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()

bcrypt = Bcrypt()


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, unique=True, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)

    collection = db.relationship("User_Pack", backref="user")

    @classmethod
    def register(cls, username, pwd, email):
        """Register a new User"""

        hashed = bcrypt.generate_password_hash(pwd)
        hashed_utf8 = hashed.decode("utf8")

        u = User(username= username, password=hashed_utf8, email=email)        
        db.session.add(u)
        return u

    @classmethod
    def authenticate(cls, username, pwd):
        """Verify a returning User"""

        u = User.query.filter_by(username=username).first()

        if u and bcrypt.check_password_hash(u.password, pwd):
            db.session.add(u)
            return u
        else:
            return False


class User_Pack(db.Model):
    __tablename__ = "users_packs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    pack_id = db.Column(db.Text, nullable=False)
    pack_name = db.Column(db.Text,nullable=False)
    

class Deck(db.Model):
    __tablename__ = "decks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    deck_name = db.Column(db.Text, nullable=False)
    faction_name = db.Column(db.Text, nullable=False)
    invest_name = db.Column(db.Text, nullable=False)
    size = db.Column(db.Integer, nullable=False, default=30)

    cards = db.relationship("Deck_Card", backref="deck")

class Deck_Card(db.Model):
    __tablename__ = "decks_cards"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    deck_id = db.Column(db.Integer, db.ForeignKey("decks.id"))
    card_id = db.Column(db.Text, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    card_name = db.Column(db.Text, nullable=False)