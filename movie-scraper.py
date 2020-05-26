import datetime
import requests
import json

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
        all_titles.extend(list(get_page_data(cat_page)))
        cm_continue = get_cm_continue(cat_page)

        if cm_continue:
            BASE_PARAMS['cmcontinue'] = cat_page['continue']['cmcontinue']

        else:
            return all_titles


def main():
    with requests.session() as session:
        all_data = {}
        for year in range(START_YEAR, END_YEAR+1):
            print(f'Getting movies from {year}')
            all_data[year] = get_year_results(session, year)

    with open('./data/all_movies.json', 'w', encoding='utf-8') as json_out:
        json.dump(all_data, json_out, indent=4)


if __name__ == '__main__':
    main()
