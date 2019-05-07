import pickle
from clize import run
from redis import Redis
from sqlitedict import SqliteDict, SqliteMultithread
from pprint import pprint
from toolz.curried import *
import log


class RedisDB:
    def __init__(self):
        self.redis = Redis()

    def get(self, key, raw=False):
        value = self.redis.get(key)
        if value is not None:
            return pickle.loads(value) if not raw else value
        return None

    def set(self, key, value, ex=None):
        self.redis.set(key, pickle.dumps(value), ex=ex)

    def incr(self, key):
        self.redis.incr(key)

    def keys(self, pattern):
        return self.redis.keys(pattern)

    def delete(self, key):
        return self.redis.delete(key)


db = RedisDB()
# db = SqliteDict('atp.db')


def get_db():
    return SqliteDict("atp.db")


def build_tournament_key(year, slug, code):
    return compose("|".join, map(str))(["tournaments", year, slug, code])


def reverse_tournament_key(key):
    return key.split("|")[1:]


def get_tournament_keys(year):
    """ Get all tournament keys for specific year

    :param year: Tournament year
    """
    return db.keys("|".join(["tournaments", str(year), "*"]))


def build_match_key(match):
    get_default_code = compose(
        "".join,
        mapcat(str_split(" ")),
        juxt(get_in(["winner", "full_name"]), get_in(["looser", "full_name"])),
    )
    return compose("|".join, map(str))(
        concatv(
            ["match"],
            juxt(
                get("tournament_year"),
                get("tournament_slug"),
                get("tournament_code"),
                lambda match: get("code")(match) or get_default_code(match),
            )(match),
        )
    )


def get_match_keys(year):
    """ Get all match keys for specific year

    :params year: Tournament year
    """
    return filter(str_startswith("|".join(["match", year])))(db.keys())


def build_player_key(slug, code):
    return compose("|".join, map(str))(("player", slug, code))


def get_player_keys():
    return filter(str_startswith("player"))(db.keys())


def get_tournament(key):
    try:
        return db[key]
    except KeyError:
        log.error("Key not found")
        return {}


def get_by_key(key):
    return pprint(db.get(key))


if __name__ == "__main__":
    run(
        compose(pprint, list, get_tournament_keys),
        compose(pprint, get_tournament),
        build_tournament_key,
        build_match_key,
        compose(pprint, list, get_match_keys),
        get_by_key,
        compose(pprint, list, get_player_keys),
    )
