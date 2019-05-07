from datetime import datetime
from clize import run
from toolz.curried import *
from request import request_html
from pq import *
from utils import *
from constants import ATP_PREFIX, tournament_category_map
from countries import countries_code_map
import log


def tournaments_list(url, from_cache=True):
    html = request_html(url, from_cache=from_cache)

    get_name = compose(pq_text, pq_find(".tourney-title"))
    get_location = compose(
        lambda location: [None, location[0]]
        if len(location) == 1
        else [location[0], location[-1]],
        list,
        map(str.strip),
        str_split(","),
        pq_text,
        pq_find(".tourney-location"),
    )
    get_dates = compose(
        datetime.isocalendar,
        lambda date: datetime(*date),
        map(int),
        map(str.strip),
        str_split("."),
        pq_text,
        pq_find(".tourney-dates"),
    )
    get_url = compose(resolve_url, pq_attr("href"), pq_eq(-1), pq_find("td a"))
    get_id = compose(juxt(get(6, default=""), get(7, default="")), str_split("/"))

    get_surface = compose(
        juxt(get(0, default=""), get(1, default="")),
        str_split(" "),
        str.lower,
        pq_text,
        pq_eq(4),
        pq_find("td"),
    )

    get_category = compose(
        flip(get(default=None))(tournament_category_map),
        get(0),
        str_split("."),
        get(-1),
        str_split("categorystamps_"),
        pq_attr("src"),
        pq_eq(0),
        pq_find("td img"),
    )

    def get_tournament_data(element):
        url = get_url(element)
        name = get_name(element)
        if not url:
            log.warning("{} is not started yet".format(name))
            # tournament in future
            return

        slug, code = get_id(url)
        city, country = get_location(element)
        year, week, _ = get_dates(element)
        surface_type, surface = get_surface(element)
        category = get_category(element)

        return dict(
            id=f"{year}-{code}",
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

    return compose(
        list,
        filter(identity(None)),
        map(get_tournament_data),
        pq_find(".tourney-result"),
    )(html)


def tournament_detail(url, from_cache=True):
    html = request_html(url, from_cache=from_cache)

    get_dates = compose(
        map(lambda date: datetime(*date).date()),
        map(map(int)),
        map(str_split(".")),
        map(str.strip),
        str_split("-"),
        pq_text,
        pq_find(".tourney-result .tourney-dates"),
    )
    try:
        date_start, date_end = get_dates(html)
        return dict(date_start=date_start, date_end=date_end)
    except ValueError:
        return {}


split_player_url = compose(str_split("/"), pq_attr("href"))
get_player_slug = compose(get(3, default=None), split_player_url)
get_player_code = compose(get(4, default=None), split_player_url)


def matches_list_per_tournament(url, from_cache=True):
    html = request_html(url, from_cache=from_cache)

    def get_left_right(default):
        return juxt(get(0, default=default), get(1, default=default))

    get_player_seed = compose(str_strip("()"), pq_text)
    get_players_seed = compose(list, map(get_player_seed), pq_find(".day-table-seed"))

    # TODO Log non recognized country
    get_player_country = compose(
        flip(get(default=None))(countries_code_map),
        str.upper,
        get(0),
        str_split("."),
        get(-1),
        str_split("/"),
        pq_attr("src"),
    )
    get_players_country = compose(
        get_left_right(None),
        list,
        map(get_player_country),
        pq_find(".day-table-flag img"),
    )

    get_is_winner_left = compose(
        lambda result: result == "Defeats",
        pq_text,
        pq_find(".day-table-vertical-label"),
    )

    get_player_url = compose(resolve_url, pq_attr("href"))
    get_player_details = compose(
        dict,
        curry(zip, ["full_name", "url", "slug", "code"]),
        juxt(pq_text, get_player_url, get_player_slug, get_player_code),
    )
    get_players_details = compose(
        get_left_right({}), list, map(get_player_details), pq_find(".day-table-name a")
    )

    get_match_code = compose(
        get(5, default=None),
        excepts(TypeError, str_split("/"), lambda _: ""),
        pq_attr("href"),
        pq_find(".day-table-score a"),
    )

    def parse_set_score(score):
        if score in ["(W/O)", "(RET)"] or len(score) == 2:
            return score
        if len(score) < 2 or len(score) > 4:
            log.warning("New match score type {} for key {}".format(score, key))
            return score
        return "{}({})".format(score[:2], score[2:])

    get_score = compose(
        " ".join,
        map(parse_set_score),
        str_split(" "),
        str_strip("()"),
        pq_text,
        pq_find(".day-table-score"),
    )

    get_url = compose(resolve_url, pq_attr("href"), pq_find(".day-table-score a"))

    get_match_order = compose(pq_text, pq_prev, pq_parents("tbody"))

    def get_match(match):
        left_seed, right_seed = get_players_seed(match)
        left_country, right_country = get_players_country(match)
        is_winner_left = get_is_winner_left(match)
        left_player, right_player = get_players_details(match)
        score = get_score(match)
        url = get_url(match)
        code = get_match_code(match)
        order = get_match_order(match)

        left = dict(seed=left_seed, country=left_country, **left_player)
        right = dict(seed=right_seed, country=right_country, **right_player)
        result = dict(score=score, code=code, order=order, url=url)
        if is_winner_left:
            result["winner"] = left
            result["looser"] = right
        else:
            result["winner"] = right
            result["looser"] = left

        return result

    return compose(list, map(get_match), pq_find(".day-table tbody tr"))(html)


def match_detail(url, from_cache=True):
    html = request_html(url, from_cache=from_cache)

    # Get complete players data and fix it in current match object
    get_player_details = excepts(
        TypeError,
        compose(
            dict,
            curry(zip, ["url", "full_name", "slug", "code"]),
            juxt(
                compose(resolve_url, pq_attr("href")),
                pq_text,
                get_player_slug,
                get_player_code,
            ),
        ),
        {},
    )

    get_winner = compose(
        get_player_details,
        pq_find(".match-stats-score-container td.won-game a.scoring-player-name"),
    )

    get_looser = compose(
        get_player_details,
        pq_find(".match-stats-score-container td:not(.won-game) a.scoring-player-name"),
    )

    winner = get_winner(html)
    looser = get_looser(html)

    get_is_winner_left = compose(
        le(0),
        curry(str.find)(winner["url"]),
        pq_attr("href"),
        pq_find(".match-stats-player-left .player-left-name a"),
    )

    get_time = compose(pq_text, pq_find(".match-info-row .time"))

    def parse_score(score_q):
        breakdown = pq_find(".stat-breakdown")(score_q)
        if breakdown:
            return compose(
                dict,
                curry(zip, ["won", "total"]),
                str_split("/"),
                str_strip("()"),
                pq_text,
            )(breakdown)
        return {"total": score_q.text()}

    is_winner_left = get_is_winner_left(html)
    left_name = "winner" if is_winner_left else "looser"
    right_name = "looser" if is_winner_left else "winner"
    get_player_stats = compose(
        dict,
        curry(zip, [left_name, right_name, "label"]),
        juxt(
            compose(parse_score, pq_find(".match-stats-number-left")),
            compose(parse_score, pq_find(".match-stats-number-right")),
            compose(pq_text, pq_find(".match-stats-label")),
        ),
    )
    get_players_stats = compose(
        list, map(get_player_stats), pq_find(".match-stats-table tr.match-stats-row")
    )
    return dict(
        duration=get_time(html),
        winner=winner,
        looser=looser,
        stats=get_players_stats(html),
    )


def player_detail(url, from_cache=True):
    html = request_html(url, from_cache=from_cache)

    get_basic_detail = compose(
        dict,
        curry(zip, ["birth_date", "turned_pro", "weight", "height"]),
        juxt(
            compose(
                str_replace(".", "-"),
                str_strip("()"),
                pq_text,
                pq_find(".table-birthday"),
            ),
            compose(pq_text, pq_find(".table-big-value"), pq_eq(1)),
            compose(
                str_strip("kg"),
                str_strip("()"),
                pq_text,
                pq_find(".table-weight-kg-wrapper"),
            ),
            compose(
                str_strip("cm"),
                str_strip("()"),
                pq_text,
                pq_find(".table-height-cm-wrapper"),
            ),
        ),
        pq_find(".player-profile-hero-table tr:first-child td"),
    )

    def get_country_from_text(text):
        country = countries_code_map.get(text)

        if not country:
            log.warning(f"Country code {text} for player url:{url} not found")
            return None
        return country

    get_country = compose(
        get_country_from_text,
        pq_text,
        pq_find(".player-profile-hero-dash .player-flag-code"),
    )

    return dict(get_basic_detail(html), country=get_country(html))


if __name__ == "__main__":
    run(
        tournaments_list,
        tournament_detail,
        matches_list_per_tournament,
        match_detail,
        player_detail,
    )

