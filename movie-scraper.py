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


def get_cm_continue(data):
    try:
        return data['continue']['cmcontinue']
    except KeyError:
        return None


def get_cat_data(session, params):
    results = session.get(url=BASE_URL, params=params)
    return results.json()


def get_titles(data):
    for page in data['query']['categorymembers']:
        if not page['title'].startswith('Category:'):
            yield page['title']


def get_year_results(session, year):
    BASE_PARAMS['cmtitle'] = f"Category:{year}_films"
    BASE_PARAMS['cmcontinue'] = ""

    all_titles = []

    while True:
        cat_page = get_cat_data(session, BASE_PARAMS)
        all_titles.extend(list(get_titles(cat_page)))
        cm_continue = get_cm_continue(cat_page)

        if cm_continue:
            BASE_PARAMS['cmcontinue'] = cat_page['continue']['cmcontinue']

        else:
            return all_titles


def main():
    with requests.session() as session:
        all_data = {}
        for year in range(START_YEAR, END_YEAR+1):
            print(f'getting movies from {year}')
            all_data[year] = get_year_results(session, year)

    with open('./data/all_movies.json', 'w', encoding='utf-8') as json_out:
        json.dump(all_data, json_out)


if __name__ == '__main__':
    main()
