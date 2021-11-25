import requests
from flask import Flask, request, render_template, redirect, session, flash, g, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, User_Pack, Deck, Deck_Card
from forms import RegisterForm, LoginForm, DeckForm



app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///arkham"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "canilive"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


connect_db(app)
base_url = "https://arkhamdb.com/api/public"

toolbar = DebugToolbarExtension(app)
CURR_USER_KEY = "curr_user"

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


#*****************************************************************************
#
# Registration and Login/Logout Routes
#
#*****************************************************************************
@app.route("/")
def home():
    """The home page"""

    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registration page"""

    form = RegisterForm()
    if form.validate_on_submit():
        user = User.register(
            username=form.username.data,
            email=form.email.data,
            pwd=form.password.data
        )
        db.session.commit()
        do_login(user)
        return redirect(f"users/{user.id}/setup")

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""

    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data,
            form.password.data
        )
        db.session.commit()
        do_logout()
        do_login(user)
        return redirect(f"users/{user.id}")

    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    """Logout Current User"""

    do_logout()
    return redirect("/")


#*****************************************************************************
#
# User and Collection Routes
#
#*****************************************************************************

@app.route("/users/<int:user_id>")
def user_home(user_id):
    """User home page"""
    if not g.user:
        return redirect("/")
    if g.user.id  != user_id:
        flash("Access unauthorized.")
        return redirect(f"/users/{g.user.id}")

    user = User.query.get_or_404(user_id)
    
    return render_template("user_home.html", user=user)

@app.route("/users/<int:user_id>/setup")
def coll_setup(user_id):
    """Initial set up of a users collection"""
    if not g.user:
        return redirect("/")
    if g.user.id  != user_id:
        flash("Access unauthorized.")
        return redirect(f"/users/{g.user.id}")

    user = User.query.get_or_404(user_id)

    resp = requests.get(f'{base_url}/packs/')
    packs = resp.json()
    sorted_packs = sorted(packs, key=sort_packs)

    return render_template("collection.html", packs=sorted_packs, user=user)

@app.route("/collection/add", methods=["POST"])
def coll_add():
    """Add a pack to a users collection"""
    
    coll = [p.pack_id for p in g.user.collection]
    data = request.json
    
    if data["pack_code"] in coll:
        pack_out = User_Pack.query.filter(User_Pack.pack_id == data["pack_code"], User_Pack.user_id  == g.user.id).first()
        db.session.delete(pack_out)
    else:
        new_pack = User_Pack(user_id=g.user.id, pack_id=data["pack_code"], pack_name=data["pack_name"])
        g.user.collection.append(new_pack)
    
    db.session.commit()

    return ("added", 201)


def sort_packs(value):
    return value["cycle_position"]

#*****************************************************************************
#
# Deck and Card Routes
#
#*****************************************************************************


@app.route("/decks/setup", methods=["GET","POST"])
def deck_setup():
    """Pick an investigator and initialize a new deck"""
    if not g.user:
        return redirect("/")

    form = DeckForm()
    coll = [p.pack_id for p in g.user.collection]
    cards = []
    sorted_cards = []
    names = []
    investigator = {}

    for code in coll:
        resp = requests.get(f'{base_url}/cards/{code}')
        cards = cards + resp.json()
    for card in cards:
        if card["type_code"] == "investigator":
            sorted_cards.append(card)
            names.append(card["name"])
    form.invest_name.choices = names
    if form.validate_on_submit():
        for card in sorted_cards:
            if card["name"] == form.invest_name.data:
                investigator = card
        deck = Deck(
            user_id = g.user.id,
            deck_name = form.deck_name.data,
            faction_name = investigator["faction_name"],
            invest_id = investigator["code"],
            invest_name = form.invest_name.data
        )
        db.session.add(deck)
        db.session.commit()
        return redirect(f"/decks/{deck.id}/build")
    return render_template("deck_setup.html", form=form, cards=sorted_cards)

@app.route("/decks/<int:deck_id>/build")
def deck_build(deck_id):
    """Build a deck"""
    deck = Deck.query.get(deck_id)
    if not g.user:
        return redirect("/")
    if g.user.id  != deck.user.id:
        flash("Access unauthorized.")
        return redirect(f"/users/{g.user.id}")

    investigator = requests.get(f'{base_url}/card/{deck.invest_id}')
    investigator = investigator.json()

    coll = [p.pack_id for p in g.user.collection]
    cards = []
    sorted_cards = []
    factions = []
    
    for code in coll:
        resp = requests.get(f'{base_url}/cards/{code}')
        cards = cards + resp.json()
    # Deck building currently excludes neutral cards, investigator signiture cards, weaknesses, investegators with optional secondary classes and trait specific deck requirments 
    # Deck size is also set to 30 automatically.  
    # These functions will be added or ammended in future versions.
    for option in investigator["deck_options"]:
        for faction in option:
            if faction == "faction":
                for faction2 in option[faction]:
                    if faction2 != "neutral":
                        factions.append(faction2)

    for card in cards:
        if card["faction_code"] in factions and card["deck_limit"] != 0:
                if card["type_code"] != "investigator":
                    if "xp" in card:
                        if card["xp"] == 0:
                            sorted_cards.append(card)
    in_deck = {}
    for pick in deck.cards:
        in_deck[pick.card_id] = pick.qty
    
    return render_template("deck_build.html", cards=sorted_cards, deck=deck, in_deck = in_deck)


@app.route("/decks/<int:deck_id>/add", methods=["POST"])
def add_to_deck(deck_id):
    """add a card to a deck"""

    data = request.json
    deck = Deck.query.get_or_404(deck_id)
    
    card_ids = [c.card_id for c in deck.cards]
    
    card = Deck_Card(
        deck_id = data["int_deck_id"],
        card_id = data["card_id"],
        qty = data["int_qty"],
        card_name = data["card_name"]
    ) 

    if data["int_qty"] == 0:
        card_out = Deck_Card.query.filter(Deck_Card.card_id == data["card_id"], Deck_Card.deck_id  == deck_id).first()
        db.session.delete(card_out)

    elif data["card_id"] in card_ids:
        card_out = Deck_Card.query.filter(Deck_Card.card_id == data["card_id"], Deck_Card.deck_id  == deck_id).first()
        db.session.delete(card_out)
        db.session.add(card)

    else:    
        db.session.add(card)

    db.session.commit()
    total = Deck.count(deck_id)
    count = { 
        "total": total,
        "legal": "Deck Minimmum Not Met"
    }
    if total > deck.size:
        count = { 
            "total": total,
            "legal": "Too Many Cards"
        }
    
    elif total == deck.size:
        count = { 
        "total": total,
        "legal": "Deck Size Okay"
    }

    return (count, 201)

@app.route("/decks/<int:deck_id>")
def deck_info(deck_id):
    """Show deck info"""

    deck = Deck.query.get_or_404(deck_id)
    return render_template("deck_info.html", deck=deck)
   
@app.route("/cards/<card_id>/<int:deck_id>")
def card_info(card_id, deck_id):
    """Show available card information"""
    deck = Deck.query.get_or_404(deck_id)
    resp = requests.get(f'{base_url}/card/{card_id}')
    card = resp.json()

    return render_template("card_info.html", card=card, deck=deck)