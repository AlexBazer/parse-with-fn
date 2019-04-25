from clize import run

import log
from toolz.curried import *
from request import request_html
from pq import *
from utils import *
from db import db, get_player_keys


def players_details(from_cache=True):
    """Parse additional player info.

    For now if player was already parsed with player_detail parser, simply skip him
    """
    log.info('Parse players details')

    run_in_pool(
        curry(player_detail, from_cache=from_cache),
        get_player_keys(),
        'Parse players details'
    )


@log_exception
def player_detail(key, from_cache=True):
    player = db[key]
    url = player['url']
    log.debug('{}:{} parse player detail'.format(key, url))

    if not url:
        log.warning('{} player does not have details'.format(key))
        return

    q = PyQuery(request_html(url, from_cache=from_cache))

    get_basic_detail = compose(
        dict,
        curry(zip, ['birth_date', 'turned_pro', 'weight', 'height']),
        juxt(
            compose(
                str_replace('.', '-'),
                str_strip('()'),
                pq_text,
                pq_find('.table-birthday'),
            ),
            compose(
                pq_text,
                pq_find('.table-big-value'),
                pq_eq(1)
            ),
            compose(
                str_strip('kg'),
                str_strip('()'),
                pq_text,
                pq_find('.table-weight-kg-wrapper'),
            ),
            compose(
                str_strip('cm'),
                str_strip('()'),
                pq_text,
                pq_find('.table-height-cm-wrapper'),
            )
        ),
        pq_find('.player-profile-hero-table tr:first-child td')
    )

    result = get_basic_detail(q)

    db[key] = merge(player, result)
    track_lacked(key, url, result)


if __name__ == '__main__':
    run(player_detail, players_details)
