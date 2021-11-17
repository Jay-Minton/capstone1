import os
from unittest import TestCase
from sqlalchemy import exc
 
from models import db, User, User_Pack, Deck, Deck_Card

os.environ['DATABASE_URL'] = "postgresql:///arkham-test"
 
 
from app import app

db.create_all()
 
 
class UserModelTestCase(TestCase):
    """Test models."""
 
    def setUp(self):
        """Create test client, add sample data."""
 
        db.drop_all()
        db.create_all()
 
        u1 = User.register("test_user_1", "password", "u1@email.com")
        u1id = 11
        u1.id = u1id
 
        db.session.commit()
 
        u1 = User.query.get(u1id)
 
        self.u1 = u1
        self.u1id = u1id
 
        self.client = app.test_client()
 
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_user_add_pack(self):
        pack = User_Pack(
            user_id = self.u1id,
            pack_id = "bota",
            pack_name = "Blood On The Altar"
        )

        db.session.add(pack)
        db.session.commit()

        self.assertEqual(len(self.u1.collection), 1)

    def test_user_create_deck(self):
        deck = Deck(
            user_id = self.u1id,
            invest_name = "test invest",
            invest_id = "test id",
            deck_name = "test name",
            faction_name = "test faction",
        )

        db.session.add(deck)
        db.session.commit()
        
        self.assertEqual(len(self.u1.decks), 1)

    def test_deck_add_card(self):
        deck = Deck(
            user_id = self.u1id,
            invest_name = "test invest",
            invest_id = "test id",
            deck_name = "test name",
            faction_name = "test faction",
        )

        db.session.add(deck)
        db.session.commit()

        card = Deck_Card(
            deck_id = deck.id,
            card_id = "test id",
            qty = 2,
            card_name = "test name"
        )
        
        db.session.add(card)
        db.session.commit()
        
        self.assertEqual(len(deck.cards), 1)
        self.assertEqual(Deck.count(deck.id), 2)

    def test_register(self):
        u3 = User.register("test_user_3", "password", "u3@email.com",)
        u3id = 33
        u3.id = u3id
        db.session.add(u3)
        db.session.commit()
 
        u3 = User.query.get(u3id)
        self.assertIsNotNone(u3)
        self.assertEqual(u3.username, "test_user_3")
        self.assertEqual(u3.email, "u3@email.com")
        self.assertNotEqual(u3.password, "password")

    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.u1id)

    def test_invalid_email(self):
        email = User.register("user", "password", None)
        uid = 44
        email.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
 
    def test_invalid_name(self):
        name = User.register(None, "test@email.com", "password")
        uid = 55
        name.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
 
    def test_invalid_password(self):
        with self.assertRaises(ValueError) as context:
            User.register("testtest", "", "email@email.com")
        
        with self.assertRaises(ValueError) as context:
            User.register("testtest", None, "email@email.com")