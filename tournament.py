from datetime import datetime
from clize import run
from request import request_html
from db import db
from pq import *
from toolz.curried import *

from countries import countries_code_map

from operator import attrgetter, add
from constants import ATP_PREFIX

str_split = flip(str.split)
str_startswith = flip(str.startswith)
str_strip = flip(str.strip)

def log_warning(msg):
    print(msg)

def build_tournament_key(year, slug, code):
    return compose(
        '|'.join,
        map(str),
    )(['tournaments', year, slug, code])

def reverse_tournament_key(key):
    return key.split('|')[1:]

def get_tournaments_keys(year):
    return filter(
        str_startswith('|'.join(['tournaments', year]))
    )(db.keys())

def tournaments_per_year(year, from_cache=True):
    url = 'https://www.atptour.com/en/scores/results-archive?year={}'.format(year)

    q = PyQuery(request_html(url, from_cache=from_cache))

    get_name = compose(
        pq_text,
        pq_find('.tourney-title'),
    )
    get_location = compose(
        list,
        map(str.strip),
        str_split(','),
        pq_text,
        pq_find('.tourney-location')
    )
    get_dates = compose(
        datetime.isocalendar,
        lambda date: datetime(*date),
        map(int),
        map(str.strip),
        str_split('.'),
        pq_text,
        pq_find('.tourney-dates')
    )
    get_url = compose(
        excepts(
            TypeError,
            partial(add, ATP_PREFIX),
            lambda _: '',
        ),
        pq_attr('href'),
        pq_eq(-1),
        pq_find('td a'),
    )
    get_id = compose(
        juxt(get(6, default=''), get(7, default='')),
        str_split('/')
    )

    get_surface = compose(
        juxt(get(0, default=''), get(1, default='')),
        str_split(' '),
        str.lower,
        pq_text,
        pq_eq(4),
        pq_find('td'),
    )
    result = {}
    for one_result in q.find('.tourney-result'):
        url = get_url(one_result)
        name = get_name(one_result)

        if not url:
            print('{} is not started yet'.format(name))
            # tournament in future
            continue

        slug, code = get_id(url)
        city, country = get_location(one_result)
        year, week, _ = get_dates(one_result)
        surface_type, surface = get_surface(one_result)

        one = dict(
            slug=slug,
            code=code,
            name=name,
            city=city,
            country=country,
            year=year,
            week=week,
            url=url,
            type=surface_type,
            surface=surface,
        )
        print('{} {} is parsed'.format(name, year))
        db[build_tournament_key(year, slug, code)] = one


def tournaments_details(year):
    [tournament_detail(key) for key in get_tournaments_keys(year)]

def tournament_detail(key):
    tournament = db[key]
    html = request_html(tournament['url'])

    get_dates = compose(
        map(lambda date: datetime(*date).date()),
        map(map(int)),
        map(str_split('.')),
        map(str.strip),
        str_split('-'),
        pq_text,
        pq_find('.tourney-result .tourney-dates')
    )

    date_start, date_end = get_dates(html)

    db[key] = dict(
        tournament,
        date_start=date_start,
        date_end=date_end,
    )
    print('{} {} parse additional data'.format(tournament['name'], tournament['year']))


def get_match_key(match):
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
            get_in(['winner', 'slug']),
            get_in(['winner', 'code']),
            get_in(['looser', 'slug']),
            get_in(['looser', 'code']),
        )(match)
    ))

def matches_per_tournament(key, from_cache=False):
    tournament = db[key]
    url = tournament['url']
    q = PyQuery(request_html(url, from_cache=from_cache))

    get_player_seed = compose(
        str_strip('()'),
        pq_text,
    )
    get_players_seed = compose(list, map(get_player_seed), pq_find('.day-table-seed'))

    get_player_country = compose(
        flip(get)(countries_code_map),
        str.upper,
        get(0),
        str_split('.'),
        get(-1),
        str_split('/'),
        pq_attr('src'),
    )
    get_players_country = compose(list, map(get_player_country), pq_find('.day-table-flag img'))

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
    get_players_details = compose(list, map(get_player_details), pq_find('.day-table-name a'))

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
            log_warning('New match score type {} for key {}'.format(score, key))
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
        tournament_year, tournament_slug, tournament_code = reverse_tournament_key(key)
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
        print(get_match_key(result))
        db[get_match_key(result)] = result

if __name__ == '__main__':
    run(tournaments_per_year, tournaments_details, tournament_detail, matches_per_tournament)
