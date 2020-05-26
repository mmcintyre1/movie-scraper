import datetime
import re
import json

import requests

START_YEAR = 1874
END_YEAR = datetime.datetime.today().year

BASE_URL = "https://en.wikipedia.org/w/api.php"
BASE_PARAMS = {
    "action": "query",
    "cmlimit": 500,
    "list": "categorymembers",
    "format": "json",
}


# TODO clean up titles (film) (year film)
# TODO get more metadata from results
# TODO write parsers to go to page and get acting list
# TODO clean up that acting list


def get_year_results(session, year):
    """
    Top level wrapper function to iterate through all the
    years between the global START_YEAR and END_YEAR and extend
    the all_titles list. Takes care of page continuations via the
    cm_continue key in BASE_PARAMS.
    :param session: a requests session object
    :param year: a year to find movie categories for
    :return: a list of all movie data per year
    """
    BASE_PARAMS['cmtitle'] = f"Category:{year}_films"
    BASE_PARAMS['cmcontinue'] = ""

    all_titles = []

    while True:
        cat_page = get_cat_data(session, BASE_PARAMS)
        for page_data in get_page_data(cat_page):
            all_titles.append({
                'title': clean_title(page_data['title']),
                'actors': get_actor_data(page_data['pageid'])
            })

        cm_continue = get_cm_continue(cat_page)

        if cm_continue:
            BASE_PARAMS['cmcontinue'] = cat_page['continue']['cmcontinue']

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
        if not page['title'].startswith('Category:'):
            yield page


def get_actor_data(pageid):
    """
    Takes in a page_id, which is returned from
    :param pageid:
    :return:
    """
    return []


def clean_title(title):
    """
    Cleans up parentheses in title, such as Title A (2013 film) or
    Title B (film).  It hasn't been tested on any other type.
    :param title: a string
    :return: a cleaned up title string
    """
    film_pattern = r"\([0-9]{0,4}\s{0,1}film\)"
    return re.sub(film_pattern, "", title)


def main():
    with requests.session() as session:
        all_data = {}
        for year in range(START_YEAR, END_YEAR + 1):
            print(f'Getting movies from {year}')
            all_data[year] = get_year_results(session, year)

    with open('./data/all_movies.json', 'w') as json_out:
        json.dump(all_data, json_out, indent=4)


if __name__ == '__main__':
    main()
