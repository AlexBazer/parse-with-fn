import pickledb
import requests

db = pickledb.load('html.cached.db')

def tournaments_per_year(year):
    url = 'https://www.atptour.com/en/scores/results-archive?year={}&json=true'.format(year)
    response = yield requests.get(url)
    if response.ok:
        yield db.set(url, response.content)



