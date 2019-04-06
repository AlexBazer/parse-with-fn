from clize import run
from toolz.curried import *
from request import request_html
from constants import ATP_PREFIX
from pq import *
from utils import *
from db import db, build_match_key, reverse_tournament_key
from countries import countries_code_map
import log


def matches_per_tournament(key, from_cache=False):
    tournament = db[key]
    url = tournament['url']
    q = PyQuery(request_html(url, from_cache=from_cache))

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
        list, map(get_player_country), pq_find('.day-table-flag img'))

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
        get(3),
        split_player_url
    )
    get_player_code = compose(
        get(4),
        split_player_url
    )
    get_player_url = compose(
        curry(add, ATP_PREFIX),
        pq_attr('href')
    )
    get_player_details = compose(
        dict,
        curry(zip, ['full_name', 'url', 'slug', 'code']),
        juxt(pq_text, get_player_url, get_player_slug, get_player_code),
    )
    get_players_details = compose(
        list, map(get_player_details), pq_find('.day-table-name a'))

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

    def parse_match_set_score(score):
        if score == '(W/O)' or len(score) == 2:
            return score
        if len(score) < 2 or len(score) > 3:
            log.warning(
                'New match score type {} for key {}'.format(score, key))
            return score
        return '{}({})'.format(score[:-1], score[-1])

    get_match_score = compose(
        ' '.join,
        map(parse_match_set_score),
        str_split(' '),
        pq_text,
        pq_find('.day-table-score')
    )

    get_match_order = compose(
        pq_text,
        pq_prev,
        pq_parents('tbody')
    )

    for match in q.find('.day-table tbody tr'):
        left_seed, right_seed = get_players_seed(match)
        left_country, right_country = get_players_country(match)
        is_winner_left = get_is_winner_left(match)
        left_player, right_player = get_players_details(match)
        score = get_match_score(match)
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
        tournament_year, tournament_slug, tournament_code = reverse_tournament_key(
            key)
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
        print(build_match_key(result))
        db[build_match_key(result)] = result


if __name__ == '__main__':
    run(matches_per_tournament)
