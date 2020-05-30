import datetime
import json
import logging
import re
import requests
import sys

import make_actor_lookup

LOG = logging.getLogger(__name__)
START_YEAR = 1920
# END_YEAR = datetime.datetime.today().year
END_YEAR = 1922

BASE_URL = "https://en.wikipedia.org/w/api.php"
HEADER = {
    "User-Agent": "movie-scraper/1.0 (mfmcintyre01@gmail.com) python/3.8"
}


def get_year_results(session, year):
    """
    Top level wrapper function to iterate through all the
    years between the global START_YEAR and END_YEAR and extend
    the all_titles list.  If there is a cmcontinue, that signals
    there are more results, and the function iterates until that
    value is empty in the response.
    :param session: a requests session object
    :param year: a year to find movie categories for
    :return: a list of all movie data per year
    """
    params = {
        "list": "categorymembers",
        "cmtitle": f"Category:{year}_films",
        "action": "query",
        "cmlimit": 500,
        "format": "json",
    }

    all_titles = []

    while True:
        cat_page = get_cat_data(session, params)
        for page_data in get_page_data(cat_page):
            all_titles.append({
                'title': clean_title(page_data['title']),
                'actors': get_actor_data(session, page_data['title'])
            })

        cm_continue = get_cm_continue(cat_page)

        if cm_continue:
            params['cmcontinue'] = cat_page['continue']['cmcontinue']

        else:
            return all_titles


def get_cm_continue(data):
    """
    If there is a cm_continue attribute in the response JSON, it means
    the results are paged and this value needs to be fed in the params
    to subsequent queries to get additional results.
    :param data: a JSON object returned from the wikipedia api
    :return: either the cm_continue value or None
    """
    try:
        return data['continue']['cmcontinue']
    except KeyError:
        return None


def get_cat_data(session, params):
    """
    Gets the category data per the passed in params and the global
    constant BASE_URL.
    :param session: a requests session object
    :param params: a dictionary of parameters to pass to the get request
    :return: the JSON results
    """
    results = session.get(url=BASE_URL, params=params, headers=HEADER)
    return results.json()


def get_page_data(data):
    """
    Gets the data for a page and excludes titles that start with
    'Category:' as subcategories are returned as part of the results.
    :param data: a JSON object returned from the wikipedia api
    :return: a dictionary result
    """
    for page in data['query']['categorymembers']:
        if not page['title'].startswith(('Category:', 'List of ')):
            yield page


def get_actor_data(session, title):
    """
    Gets the actor data via a movie title, which needs to be an exact
    title in wikipedia.  First, the section that the Cast is in is identified
    via a partial match on "Cast", then the wikitext is pulled down and an
    actor list is rudimentarily parsed into a list and tacked on to the actors results.
    :param session: a requests session that all get requests are executed under
    :param title: an exact wikipedia movie title match
    :return: a list of actors and if there are none an empty list
    """
    LOG.info(f"Getting actors from {title}")
    cast_section_index = get_cast_section_index(session, title)

    if cast_section_index:
        return get_cast(session, title, cast_section_index)

    return []


def get_cast_section_index(session, title):
    """
    Gets the section of the wikipedia page where the Cast information likely lives,
    using a partial match on "Cast".  It's easier than parsing the whole darn page.
    :param session: a requests session that all requests are executed under
    :param title: an exact wikipedia movie title match
    :return: an integer or None
    """
    params = {
        "action": "parse",
        "page": title,
        "prop": "sections",
        "format": "json"
    }
    section_results = session.get(BASE_URL, params=params, headers=HEADER).json()

    for section in section_results["parse"]["sections"]:
        if "Cast" in section["line"]:
            return section["index"]


def get_cast(session, title, cast_section_index):
    """
    Gets an unparsed list of wikitext from the Cast section of the page and then
    passes to the cleanup function to parse into a list of just actors and not who
    they portrayed.
    :param session: a requests session that all requests are executed under
    :param title: an exact wikipedia movie title match
    :param cast_section_index: an integer which is passed to the get request
    :return:
    """
    params = {
        "action": "parse",
        "prop": "wikitext",
        "section": cast_section_index,
        "page": title,
        "format": "json"
    }

    cast_results = session.get(BASE_URL, params=params, headers=HEADER).json()
    actors = []
    unparsed_actors = re.split("\n", cast_results["parse"]["wikitext"]["*"])

    for actor in unparsed_actors:

        cleaned = clean_actor(actor)
        if cleaned:
            actors.append(cleaned)
    LOG.debug(f"unparsed actors: {unparsed_actors}\nparsed actors: {actors}")

    return actors


def clean_actor(actor):
    """
    Brute force string cleaning at it's finest.  The three sets at the top
    will likely need to be fine-tuned, but this whole thing is really meant as
    a one-off data pull anyway.
    :param actor: an unparsed actor string
    :return: a parsed actor string
    """
    bad_characters = {"Cast", "===", "png", "jpg", "gif", "Div col"}
    removals = {"[", "]", "*", "<br>"}
    played_by_words = {" as ", "-", "....", "...", "|"}

    # remove bad entries
    if any(x in actor for x in bad_characters):
        return None

    # remove unwanted characters
    for r in removals:
        actor = actor.replace(r, "")

    # remove portrayals
    for r in played_by_words:
        actor = actor.rsplit(r, -1)[0]

    # remove parentheses
    actor = re.sub(r"\s\(.*\)", "", actor)

    return actor.strip()


def clean_title(title):
    """
    Cleans up parentheses in title, such as Title A (2013 film) or
    Title B (film).  It hasn't been tested on any other type.
    :param title: a string
    :return: a cleaned up title string
    """
    film_pattern = r"\([0-9]{0,4}\s{0,1}film\)"
    return re.sub(film_pattern, "", title).strip()


def main():
    with requests.session() as session:
        all_data = {}
        for year in range(START_YEAR, END_YEAR + 1):
            LOG.info(f'Getting movies from {year}')
            all_data[year] = get_year_results(session, year)

    with open('./data/all_movies.json', 'w', encoding="utf-8") as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)

    with open('./data/all_actors.json', 'w', encoding="utf-8") as json_file:
        actor_json = make_actor_lookup.make_actor_json(all_data)
        json.dump(actor_json, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    logging.basicConfig(
        format="%(filename)s - %(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        stream=sys.stdout
    )
    main()
