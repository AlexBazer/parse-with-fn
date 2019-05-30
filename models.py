import os
from dotenv import load_dotenv
from pony import orm

load_dotenv()

db = orm.Database()
db.bind(
    provider="oracle",
    user=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD"),
    dsn=os.getenv("DB_DSN"),
)


class Tournament(db.Entity):
    _table_ = ["TENNISANALYZER", "STG_TOURNAMENTS"]
    tourney_year_id = orm.PrimaryKey(str)
    tourney_year = orm.Optional(int)
    tourney_order = orm.Optional(int)
    tourney_name = orm.Optional(str)
    tourney_id = orm.Optional(int)
    tourney_slug = orm.Optional(str)
    tourney_location = orm.Optional(str)
    tourney_dates = orm.Optional(str)
    tourney_singles_draw = orm.Optional(int)
    tourney_doubles_draw = orm.Optional(int)
    tourney_conditions = orm.Optional(str)
    tourney_surface = orm.Optional(str)
    tourney_fin_commit = orm.Optional(str)
    tourney_url_suffix = orm.Optional(str)
    singles_winner_name = orm.Optional(str)
    singles_winner_url = orm.Optional(str)
    singles_winner_player_slug = orm.Optional(str)
    singles_winner_player_id = orm.Optional(str)
    doubles_winner_1_name = orm.Optional(str)
    doubles_winner_1_url = orm.Optional(str)
    doubles_winner_1_player_slug = orm.Optional(str)
    doubles_winner_1_player_id = orm.Optional(str)
    doubles_winner_2_name = orm.Optional(str)
    doubles_winner_2_url = orm.Optional(str)
    doubles_winner_2_player_slug = orm.Optional(str)
    doubles_winner_2_player_id = orm.Optional(str)
    country = orm.Optional(str)
    city = orm.Optional(str)


db.generate_mapping()
