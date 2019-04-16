from urllib.parse import urlencode
from datetime import datetime
from clize import run
from toolz.curried import *
from request import request_html
from db import db, build_tournament_key, get_tournament_keys
from pq import *
from utils import *
from constants import ATP_PREFIX, tournament_category_map
from countries import countries_code_map
import log


def tournaments_per_year(year, from_cache=True):
    tournaments_url = 'https://www.atptour.com/en/scores/results-archive?'

    major_tournaments = tournaments_url + urlencode({
        'year': year,
    })
    _tournaments_per_year(major_tournaments, year, from_cache=from_cache)

    challenge_tournaments = tournaments_url + urlencode({
        'year': year,
        'tournamentType': 'ch'
    })
    _tournaments_per_year(challenge_tournaments, year, from_cache=from_cache)


def _tournaments_per_year(url, year, from_cache=True):
    """
    Parse tournaments list for a specific year and store data per tournament

    :param url:
    :param year: Tournament year
    :param from_cache: Take page html form db cache
    """
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

    get_category = compose(
        flip(get(default=None))(tournament_category_map),
        get(0),
        str_split('.'),
        get(-1),
        str_split('categorystamps_'),
        pq_attr('src'),
        pq_eq(0),
        pq_find('td img')
    )

    result = {}
    for one_result in q.find('.tourney-result'):
        url = get_url(one_result)
        name = get_name(one_result)
        if not url:
            log.warning('{} is not started yet'.format(name))
            # tournament in future
            continue

        slug, code = get_id(url)
        city, country = get_location(one_result)
        year, week, _ = get_dates(one_result)
        surface_type, surface = get_surface(one_result)
        category = get_category(one_result)

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
            category=category,
        )
        log.info('{} {} is parsed'.format(name, year))
        db[build_tournament_key(year, slug, code)] = one


def tournaments_details(year, from_cache=True):
    """
    Parse each tournament for a specific year to get more deetails and store data per tournament

    :param year: Tournament year
    :param from_cache: Take page html form db cache
    """

    [tournament_detail(key, from_cache=from_cache) for key in get_tournament_keys(year)]


def tournament_detail(key, from_cache=True):
    tournament = db[key]
    html = request_html(tournament['url'], from_cache=from_cache)

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
    log.info('{} {} parse additional data'.format(
        tournament['name'], tournament['year']))


if __name__ == '__main__':
    run(tournaments_per_year, tournaments_details, tournament_detail)
