from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from flask_debugtoolbar import DebugToolbarExtension

from .helpers import provinces, countries, can_pick_up, can_drop_off, dropped_off

app = Flask(__name__)
app.config.from_object('config')
app.jinja_env.globals.update(provinces=provinces)
app.jinja_env.globals.update(countries=countries)
app.jinja_env.globals.update(can_pick_up=can_pick_up)
app.jinja_env.globals.update(can_drop_off=can_drop_off)
app.jinja_env.globals.update(dropped_off=dropped_off)
app.jinja_env.globals.update(dir=dir)
app.jinja_env.globals.update(str=str)

db = SQLAlchemy()
db.init_app(app)

#toolbar = DebugToolbarExtension(app)

from ktcs import models

user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore)

from ktcs import forms, helpers, views