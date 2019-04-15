from clize import run

import log
from toolz.curried import *
from request import request_html
from pq import *
from utils import *
from db import db

def player_detail(key, from_cache=False):
    player = db[key]
    url = player['url']

    if not url:
        log.warning('{} player does not have details'.format(key))
        return

    q = PyQuery(request_html(url, from_cache=from_cache))

    get_basic_detail = compose(
        dict,
        curry(zip, ['birth-date', 'turned_pro', 'weight', 'height']),
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

    basic_detail = get_basic_detail(q)

    db[key] = merge(player, basic_detail)
    # Correct country


if __name__ == '__main__':
    run(player_detail)
