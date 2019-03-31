from datetime import datetime
from sqlitedict import SqliteDict
from clize import run
from toolz.curried import map, get, compose, flip, juxt, partial, first, excepts, curry, identity
import requests
from pyquery import PyQuery

from operator import attrgetter, add
from constants import ATP_PREFIX

db = SqliteDict('atp.db', autocommit=True)

def request_html(url, from_cache=True):
    html = db.get(url)

    if not html or not from_cache:
        response = requests.get(url)
        html = response.text
        db[url] = html

    return html

str_split = flip(str.split)
pq_text = lambda q: PyQuery(q).text()
pq_find = curry(lambda selector, q: PyQuery(q).find(selector))
pq_eq = curry(lambda i, q: PyQuery(q).eq(i))
pq_attr = curry(lambda attr_name, q: PyQuery(q).attr(attr_name))

def get_tournament_key(year, slug, code):
    return compose(
        '|'.join,
        str,
    )([year, slug, code])

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
        db[get_tournament_key(year, slug, code)] = one


def tournament_details(year):
    pass

run(tournaments_per_year)
