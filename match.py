from clize import run
from lxml.html import HtmlElement
from toolz.curried import *
from request import request_html
from constants import ATP_PREFIX
from pq import *
from utils import *
from db import db, build_match_key, reverse_tournament_key, get_match_keys, get_tournament_keys
from countries import countries_code_map
import log

def matches_per_tournaments(year, from_cache=True):
    """
    Parse each tournament for a specific year to get basic match info and store data per match

    :param year: Tournament year
    :param from_cache: Take page html form db cache
    """
    [matches_per_tournament(key, from_cache=from_cache)
     for key in get_tournament_keys(year)]


def matches_per_tournament(key, from_cache=False):
    tournament = db[key]
    url = tournament['url']
    q = PyQuery(request_html(url, from_cache=from_cache))

    def get_left_right(default): return juxt(
        get(0, default=default), get(1, default=default))

    get_player_seed = compose(
        str_strip('()'),
        pq_text,
    )
    get_players_seed = compose(
        list, map(get_player_seed), pq_find('.day-table-seed'))

    get_player_country = compose(
        flip(get)(countries_code_map),
        str.upper,
        get(0),
        str_split('.'),
        get(-1),
        str_split('/'),
        pq_attr('src'),
    )
    get_players_country = compose(
        get_left_right(None),
        list,
        map(get_player_country),
        pq_find('.day-table-flag img')
    )

    get_is_winner_left = compose(
        lambda result: result == 'Defeats',
        pq_text,
        pq_find('.day-table-vertical-label')
    )

    split_player_url = compose(
        str_split('/'),
        pq_attr('href')
    )
    get_player_slug = compose(
        get(3, default=None),
        split_player_url
    )
    get_player_code = compose(
        get(4, default=None),
        split_player_url
    )
    get_player_url = compose(
        lambda href: add(ATP_PREFIX, href) if href and href != '#' else None,
        pq_attr('href')
    )
    get_player_details = compose(
        dict,
        curry(zip, ['full_name', 'url', 'slug', 'code']),
        juxt(pq_text, get_player_url, get_player_slug, get_player_code),
    )
    get_players_details = compose(
        get_left_right({}),
        list,
        map(get_player_details),
        pq_find('.day-table-name a')
    )

    get_match_code = compose(
        get(5, default=None),
        excepts(
            TypeError,
            str_split('/'),
            lambda _: ''
        ),
        pq_attr('href'),
        pq_find('.day-table-score a')
    )

    def parse_set_score(score):
        if score in ['(W/O)', '(RET)'] or len(score) == 2:
            return score
        if len(score) < 2 or len(score) > 4:
            log.warning(
                'New match score type {} for key {}'.format(score, key))
            return score
        return '{}({})'.format(score[:2], score[2:])

    get_score = compose(
        ' '.join,
        map(parse_set_score),
        str_split(' '),
        pq_text,
        pq_find('.day-table-score')
    )

    get_match_order = compose(
        pq_text,
        pq_prev,
        pq_parents('tbody')
    )

    tournament_year, tournament_slug, tournament_code = reverse_tournament_key(
        key)

    def get_match(match):
        left_seed, right_seed = get_players_seed(match)
        left_country, right_country = get_players_country(match)
        is_winner_left = get_is_winner_left(match)
        left_player, right_player = get_players_details(match)
        score = get_score(match)
        match_code = get_match_code(match)
        match_order = get_match_order(match)

        left = dict(
            seed=left_seed,
            country=left_country,
            **left_player
        )
        right = dict(
            seed=right_seed,
            country=right_country,
            **right_player
        )
        result = dict(
            score=score,
            code=match_code,
            order=match_order,
            tournament_year=tournament_year,
            tournament_slug=tournament_slug,
            tournament_code=tournament_code,
        )
        if is_winner_left:
            result['winner'] = left
            result['looser'] = right
        else:
            result['winner'] = right
            result['looser'] = left

        return result

    for match in q.find('.day-table tbody tr'):
        try:
            result = get_match(match)
        except:
            log.error('Error in: {}:{} tournament, with next match data: {}'.format(
                key, url, ' '.join(pq_text(match).split())))
            raise
        db[build_match_key(result)] = result


def matches_details(year):
    [match_detail(key) for key in get_match_keys(year)]


def match_detail(key):
    pass


if __name__ == '__main__':
    run(matches_per_tournament, matches_per_tournaments)
