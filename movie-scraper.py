from bs4 import BeautifulSoup
import datetime
import json
import re

import requests

# TODO write parsers to go to page and get acting list
# TODO clean up that acting list

START_YEAR = 1940
END_YEAR = datetime.datetime.today().year

BASE_URL = "https://en.wikipedia.org/w/api.php"


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
    results = session.get(url=BASE_URL, params=params)
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
    :param session:
    :param title:
    :return:
    """
    cast_section = get_cast_section(session, title)

    return []


def get_cast_section(session, title):
    """

    :param session:
    :param title:
    :return:
    """
    params = {
        "action": "parse",
        "page": title,
        "prop": "section",
    }
    results = session.get(BASE_URL, params=params)

    for section in results.json()["parse"]["sections"]:
        if "Cast" in section["line"]:
            return section["index"]


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
            print(f'Getting movies from {year}')
            all_data[year] = get_year_results(session, year)

    with open('./data/all_movies.json', 'w', encoding="utf-8") as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
