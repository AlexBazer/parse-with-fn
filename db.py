from clize import run
from sqlitedict import SqliteDict
from pprint import pprint
from toolz.curried import *
from utils import str_startswith
import log

db = SqliteDict('atp.db', autocommit=True)


def build_tournament_key(year, slug, code):
    return compose(
        '|'.join,
        map(str),
    )(['tournaments', year, slug, code])


def reverse_tournament_key(key):
    return key.split('|')[1:]


def get_tournament_keys(year):
    """ Get all tournament keys for specific year

    :param year: Tournament year
    """
    return filter(
        str_startswith('|'.join(['tournaments', year]))
    )(db.keys())


def build_match_key(match):
    return compose(
        '|'.join,
        map(str),
    )(concatv(
        ['match'],
        juxt(
            get('tournament_year'),
            get('tournament_slug'),
            get('tournament_code'),
            get('code'),
        )(match)
    ))


def get_match_keys(year):
    """ Get all match keys for specific year

    :params year: Tournament year
    """
    return filter(
        str_startswith("|".join(['match', year]))
    )(db.keys())


def build_player_key(slug, code):
    return compose(
        '|'.join,
        map(str),
    )(('player', slug, code))


def get_player_keys():
    return filter(
        str_startswith("player")
    )(db.keys())


def get_tournament(key):
    try:
        return db[key]
    except KeyError:
        log.error('Key not found')
        return {}


def get_by_key(key):
    return pprint(db.get(key))


if __name__ == "__main__":
    run(compose(pprint, list, get_tournament_keys),
        compose(pprint, get_tournament),
        build_tournament_key,
        build_match_key,
        compose(pprint, list, get_match_keys),
        get_by_key,
        compose(pprint, list, get_player_keys)
    )
