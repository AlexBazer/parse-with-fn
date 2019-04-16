from clize import run

from tournament import tournaments_per_year, tournaments_details
from match import matches_per_tournaments, matches_details
from player import players_details

def main(year, from_cache=True):
    tournaments_per_year(year, from_cache=from_cache)
    tournaments_details(year, from_cache=from_cache)

    matches_per_tournaments(year, from_cache=from_cache)
    matches_details(year, from_cache=from_cache)

    players_details(from_cache=from_cache)


if __name__ == '__main__':
    run(main)
