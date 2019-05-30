import logging
import logzero
from clize import run
from toolz.curried import *
from urllib.parse import urlencode
from utils import run_in_pool
from utils.browser import close_browsers

from page_parser import *
from db import (
    db,
    build_tournament_key,
    build_match_key,
    build_player_key,
    get_tournament_keys,
    get_match_keys,
    get_player_keys,
)


def main(year, debug=True, from_cache=True):
    if not debug:
        logzero.loglevel(logging.INFO)

    try:
        # tournaments_per_year(year, from_cache=from_cache)
        # tournaments_details(year, from_cache=from_cache)

        # matches_per_tournaments(year, from_cache=from_cache)
        # matches_details(year, from_cache=from_cache)

        players_details(from_cache=from_cache)
    finally:
        close_browsers()


def tournaments_per_year(year, from_cache=True):
    tournaments_url = "https://www.atptour.com/en/scores/results-archive?"

    major_tournaments = tournaments_url + urlencode({"year": year})

    log.info("Parse major tournaments: {}".format(year))
    tournaments = tournaments_list(major_tournaments, from_cache=from_cache)
    update_tournaments(tournaments)

    challenge_tournaments = tournaments_url + urlencode(
        {"year": year, "tournamentType": "ch"}
    )
    log.info("Parse challenge tournaments: {}".format(year))
    tournaments = tournaments_list(challenge_tournaments, from_cache=from_cache)
    update_tournaments(tournaments)


def update_tournaments(tournaments):
    for tournament in tournaments:
        key = build_tournament_key(
            tournament["year"], tournament["slug"], tournament["code"]
        )

        db.set(key, merge(db.get(key) or {}, tournament))


def tournaments_details(year, from_cache=True):
    log.info("Parse tournaments details: {}".format(year))

    run_in_pool(
        curry(update_tournament_details, from_cache=from_cache),
        get_tournament_keys(year),
        "Parse tournaments details: {}".format(year),
    )


def update_tournament_details(key, from_cache=True):
    tournament = db.get(key) or {}
    url = tournament["url"]
    if not url:
        return

    db.set(
        key,
        merge(tournament, tournament_detail(tournament["url"], from_cache=from_cache)),
    )


def matches_per_tournaments(year, from_cache=True):
    log.info("Parse matches per tournaments: {}".format(year))

    run_in_pool(
        curry(update_matches_per_tournament_details, from_cache=from_cache),
        get_tournament_keys(year),
        "Parse matches per tournaments: {}".format(year),
    )


def update_matches_per_tournament_details(key, from_cache=True):
    tournament = db.get(key)
    url = tournament["url"]
    if not url:
        return

    matches = matches_list_per_tournament(url, from_cache=from_cache)
    for item in matches:
        item = dict(
            item,
            tournament_year=tournament["year"],
            tournament_slug=tournament["slug"],
            tournament_code=tournament["code"],
        )
        match_key = build_match_key(item)
        merged_item = merge(db.get(match_key) or {}, item)
        db.set(match_key, merged_item)

        player = merged_item["winner"]
        if player.get("url"):
            player_key = build_player_key(player["slug"], player["code"])
            db.set(player_key, player)
        else:
            log.warning(f"Player without link, {url} {player}")

        player = merged_item["looser"]
        if player.get("url"):
            player_key = build_player_key(player["slug"], player["code"])
            db.set(player_key, player)
        else:
            log.warning(f"Player without link, {url} {player}")


def matches_details(year, from_cache=True):
    log.info("Parse matches details: {}".format(year))

    run_in_pool(
        curry(update_match_details, from_cache=from_cache),
        get_match_keys(year),
        "Parse matches per tournaments: {}".format(year),
        debug=True,
    )


def update_match_details(key, from_cache=True):
    match = db.get(key) or {}
    url = match["url"]
    if not url:
        return

    db.set(key, merge(match, match_detail(url)))


def players_details(from_cache=True):
    """Parse additional player info.

    For now if player was already parsed with player_detail parser, simply skip him
    """
    log.info("Parse players details")

    run_in_pool(
        curry(update_player, from_cache=from_cache),
        get_player_keys(),
        "Parse players details",
    )


def update_player(key, from_cache=True):
    player = db.get(key) or {}
    url = player["url"]
    if not url:
        return

    db.set(key, merge(player, player_detail(url, from_cache=from_cache)))


if __name__ == "__main__":
    run(main)
