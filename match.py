from datetime import timedelta
from clize import run
from lxml.html import HtmlElement
from toolz.curried import *
from request import request_html
from constants import ATP_PREFIX
from pq import *
from utils import *
from db import db, build_match_key, reverse_tournament_key, get_match_keys, get_tournament_keys, build_player_key
from countries import countries_code_map
import log
from enlighten import Counter


def resolve_url(url):
    if url and url != '#':
        return ATP_PREFIX + url

    return None


def matches_per_tournaments(year, from_cache=True):
    """
    Parse each tournament for a specific year to get basic match info and store data per match

    :param year: Tournament year
    :param from_cache: Take page html form db cache
    """
    keys = list(get_tournament_keys(year))

    progress = Counter(
        total=len(keys), desc='Parse matches per tournaments: {}'.format(year))
    for key in get_tournament_keys(year):
        matches_per_tournament(key, from_cache=from_cache)
        progress.update()


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


def matches_per_tournament(key, from_cache=True):
    tournament = db[key]
    url = tournament['url']
    log.debug('{}:{} parse matches per tournament'.format(key, url))

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
        flip(get(default=None))(countries_code_map),
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

    get_player_url = compose(
        resolve_url,
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
        str_strip('()'),
        pq_text,
        pq_find('.day-table-score')
    )

    get_url = compose(
        resolve_url,
        pq_attr('href'),
        pq_find('.day-table-score a')
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
        url = get_url(match)
        code = get_match_code(match)
        order = get_match_order(match)

        if not left_country:
            log.warning('{}:{} Cant detect COUNTRY for {}'.format(
                key, url, left_player['full_name']))
        if not right_country:
            log.warning('{}:{} Cant detect COUNTRY for {}'.format(
                key, url, right_player['full_name']))

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
            code=code,
            order=order,
            url=url,
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
        result = get_match(match)
        match_key = build_match_key(result)
        db[match_key] = result
        track_lacked(match_key, url, result)


def matches_details(year, from_cache=True):
    log.info('Parse matches details: {}'.format(year))

    keys = list(get_match_keys(year))

    progress = Counter(
        total=len(keys), desc='Parse matches details: {}'.format(year))
    for key in keys:
        match_detail(key, from_cache)
        progress.update()


def match_detail(key, from_cache=True):
    match = db[key]
    url = match['url']

    # Pass matches without url
    if not url:
        return

    log.debug('{}:{} parse match detail'.format(key, url))

    if not url:
        log.warning('{} match does not have details'.format(key))
        return

    q = PyQuery(request_html(url, from_cache=from_cache))

    # Get complete players data and fix it in current match object
    get_player_details = excepts(
        TypeError,
        compose(
            dict,
            curry(zip, ['url', 'full_name', 'slug', 'code']),
            juxt(compose(resolve_url, pq_attr('href')),
                 pq_text, get_player_slug, get_player_code),
        ), {})

    get_winner = compose(
        get_player_details,
        pq_find('.match-stats-score-container td.won-game a.scoring-player-name')
    )

    get_looser = compose(
        get_player_details,
        pq_find('.match-stats-score-container td:not(.won-game) a.scoring-player-name')
    )

    winner = get_winner(q)
    looser = get_looser(q)

    if not get_in(['winner', 'slug'])(match):
        match = update_in(match, ['winner'], flip(merge)(winner))
        db[key] = match

    if not get_in(['looser', 'slug'])(match):
        match = update_in(match, ['looser'], flip(merge)(looser))
        db[key] = match

    get_is_winner_left = compose(
        le(0),
        curry(str.find)(winner['url']),
        pq_attr('href'),
        pq_find('.match-stats-player-left .player-left-name a')
    )

    get_time = compose(
        pq_text,
        pq_find('.match-info-row .time')
    )

    def parse_score(score_q):
        breakdown = pq_find('.stat-breakdown')(score_q)
        if(breakdown):
            return compose(
                dict,
                curry(zip, ['won', 'total']),
                str_split('/'),
                str_strip('()'),
                pq_text,
            )(breakdown)
        return {'total': score_q.text()}

    is_winner_left = get_is_winner_left(q)
    left_name = 'winner' if is_winner_left else 'looser'
    right_name = 'looser' if is_winner_left else 'winner'
    get_player_stats = compose(
        dict,
        curry(zip, [left_name, right_name, 'label']),
        juxt(compose(
            parse_score,
            pq_find('.match-stats-number-left')
        ), compose(
            parse_score,
            pq_find('.match-stats-number-right')
        ), compose(
            pq_text,
            pq_find('.match-stats-label')
        ))
    )
    get_players_stats = compose(
        list,
        map(get_player_stats),
        pq_find('.match-stats-table tr.match-stats-row')
    )

    match['duration'] = get_time(q)
    match['stats'] = get_players_stats(q)
    db[key] = match
    track_lacked(key, url, match)

    # collect players info
    def get_player_key(status): return build_player_key(
        *juxt(get_in([status, 'slug']), get_in([status, 'code']))(match)
    )
    winner_key = get_player_key('winner')
    looser_key = get_player_key('looser')

    db[winner_key] = merge(db.get(winner_key, {}), match['winner'])
    track_lacked(winner_key, url, match['winner'])
    db[looser_key] = merge(db.get(looser_key, {}), match['looser'])
    track_lacked(looser_key, url, match['looser'])


if __name__ == '__main__':
    run(matches_per_tournament, matches_per_tournaments, match_detail)
