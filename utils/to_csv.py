import csv
from toolz.curried import flip, map, get, compose
from db import get_tournament_keys, db


def build_tournaments_csv(year):
    headers = ['id', 'slug', 'code', 'name', 'city', 'country', 'year', 'week', 'url', 'type', 'surface', 'category', 'date_start', 'date_end']
    keys = get_tournament_keys(year)
    objects = (db.get(key) for key in keys)
    build_csv(objects, headers, f'export/tournaments_{year}.csv')


def build_csv(objects, headers, file_name):
    with open(file_name, "w") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for obj in objects:
            row = compose(list, map(flip(get)(obj)))(headers)
            writer.writerow(row)

