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


@app.route("/")
def home():
    """The home page"""
#*****************************************************************************
#
# Registration and Login Routes
#
#*****************************************************************************

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
        do_login(user)
        return redirect(f"users/{user.id}", user=user)

    return render_template("register.html", form=form)

#*****************************************************************************
#
# User and Collection Routes
#
#*****************************************************************************

@app.route("/users/<int:user_id>")
def user_home(user_id):
    """User home page"""

@app.route("/users/<int:user_id>/setup")
def coll_setup(user_id):
    """Initial set up of a users collection"""
    user = User.query.get_or_404(user_id)

    resp = requests.get(f'{base_url}/packs/')
    packs = resp.json()
    sorted_packs = sorted(packs, key=sort_packs)

    return render_template("collection.html", packs=sorted_packs, user=user)

@app.route("/collection/<pack_code>/<pack_name>/add", methods=["POST"])
def coll_add(pack_code, pack_name):
    """Add a pack to a users collection"""
    coll = [p.pack_id for p in g.user.collection]
    if pack_code in coll:
        pack_out = User_Pack.query.filter(User_Pack.pack_id == pack_code, User_Pack.user_id  == g.user.id).first()
        db.session.delete(pack_out)
    else:
        new_pack = User_Pack(user_id=g.user.id, pack_id=pack_code, pack_name=pack_name)
        g.user.collection.append(new_pack)
    
    db.session.commit()
    return redirect(f"/users/{g.user.id}/setup")
    #in_coll = User_Pack.query.filter(User_Pack.user_id.in_(coll))

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
            invest_name = form.invest_name.data
        )
        db.session.add(deck)
        db.session.commit()
        return redirect(f"/decks/{deck.id}/build")
    return render_template("deck_setup.html", form=form, cards=sorted_cards)

@app.route("/decks/<int:deck_id>/build")
def deck_build(deck_id):
    """Build a deck"""
    coll = [p.pack_id for p in g.user.collection]
    cards = []
    sorted_cards = []
    deck = Deck.query.get(deck_id)
    for code in coll:
        resp = requests.get(f'{base_url}/cards/{code}')
        cards = cards + resp.json()
    #resp.append(requests.get(f'{base_url}/cards/{coll[1]}'))
    #cards
    #sorted_packs = sorted(packs, key=sort_packs)
    for card in cards:
        if card["faction_name"] == deck.faction_name and card["deck_limit"] != 0 and card["type_code"] != "investigator":
            sorted_cards.append(card)

    return render_template("deck_build.html", cards=sorted_cards, deck=deck)


@app.route("/decks/<int:deck_id>")
def deck_info(deck_id):
    """Show deck info"""

@app.route("/decks/<int:deck_id>/add", methods=["POST"])
def add_to_deck(deck_id):
    """add a card to a deck"""

    data = request.json
    deck = Deck.query.get_or_404(deck_id)
    #coll = [p.pack_id for p in g.user.collection]
    card_ids = [c.card_id for c in deck.cards]
    #console.log(f"******************{data['int_deck_id']}")
    card = Deck_Card(
        deck_id = data["int_deck_id"],
        card_id = data["card_id"],
        qty = data["int_qty"],
        card_name = data["card_name"]
    ) 

    if data["int_qty"] == 0:
        #pack_out = User_Pack.query.filter(User_Pack.pack_id == pack_code, User_Pack.user_id  == g.user.id).first()
        card_out = Deck_Card.query.filter(Deck_Card.card_id == data["card_id"], Deck_Card.deck_id  == deck_id).first()
        db.session.delete(card_out)

    elif data["card_id"] in card_ids:
        card_out = Deck_Card.query.filter(Deck_Card.card_id == data["card_id"], Deck_Card.deck_id  == deck_id).first()
        db.session.delete(card_out)
        db.session.add(card)

    else:    
        db.session.add(card)

    db.session.commit()

    return ("added", 201)


@app.route("/cards/<int:card_id>")
def card_info(card_id):
    """Show available card information"""

#*****************************************************************************
#
# Trial routes to be delete upon completion
#
#*****************************************************************************

#can I append resp for multiple requests.
@app.route("/practice")
def practice():
    """temp practice stuff page"""
    coll = [p.pack_id for p in g.user.collection]
    cards = []
    sorted_cards = []
    deck_array = []
    for code in coll:
        resp = requests.get(f'{base_url}/cards/{code}')
        cards = cards + resp.json()
    #resp.append(requests.get(f'{base_url}/cards/{coll[1]}'))
    #cards
    #sorted_packs = sorted(packs, key=sort_packs)
    for card in cards:
        if card["faction_code"] == "seeker":
            sorted_cards.append(card)

    return render_template("practice.html", cards=sorted_cards, deck=deck_)

@app.route("/practice2", methods={"GET","POST"})
def practice2():
    """temp practice stuff page"""
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
            invest_name = form.invest_name.data
        )
        db.session.add(deck)
        db.session.commit()
        return redirect(f"/decks/{deck.id}/build")
    return render_template("practice2.html", form=form, cards=sorted_cards)
