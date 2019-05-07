import logging
import logzero
from clize import run
from toolz.curried import *
from urllib.parse import urlencode

from match import matches_per_tournaments, matches_details
from player import players_details
from page_parser import *
from db import db, build_tournament_key, get_tournament_keys


def main(year, debug=True, from_cache=True):
    if not debug:
        logzero.loglevel(logging.INFO)

    # tournaments_per_year(year, from_cache=from_cache)
    tournaments_details(year, from_cache=from_cache)

    # matches_per_tournaments(year, from_cache=from_cache)
    # matches_details(year, from_cache=from_cache)

    # players_details(from_cache=from_cache)


def tournaments_per_year(year, from_cache=True):
    tournaments_url = "https://www.atptour.com/en/scores/results-archive?"

    major_tournaments = tournaments_url + urlencode({"year": year})

    log.info("Parse major tournaments: {}".format(year))
    tournaments = tournaments_list(major_tournaments, from_cache=from_cache)
    write_tournaments(tournaments)

    challenge_tournaments = tournaments_url + urlencode(
        {"year": year, "tournamentType": "ch"}
    )
    log.info("Parse challenge tournaments: {}".format(year))
    tournaments = tournaments_list(challenge_tournaments, from_cache=from_cache)
    write_tournaments(tournaments)


def write_tournaments(tournaments):
    [
        db.set(
            build_tournament_key(
                tournament["year"], tournament["slug"], tournament["code"]
            ),
            tournament,
        )
        for tournament in tournaments
    ]


def tournaments_details(year, from_cache=True):
    log.info("Parse tournaments details: {}".format(year))

    run_in_pool(
        curry(update_tournament_details, from_cache=from_cache),
        get_tournament_keys(year),
        "Parse tournaments details: {}".format(year),
    )


def update_tournament_details(key, from_cache=True):
    tournament = db.get(key)
    db.set(
        key,
        merge(tournament, tournament_detail(tournament["url"], from_cache=from_cache)),
    )


if __name__ == "__main__":
    run(main)
