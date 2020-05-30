from collections import defaultdict
import json


def make_actor_json(all_movie_json):
    """

    :param all_movie_json:
    :return:
    """
    final = defaultdict(dict)

    for year, movies in all_movie_json.items():
        for movie in movies:
            for actor in movie["actors"]:
                final[actor].update({movie["title"]: year})

    return final


def main():
    with open('./data/all_movies.json', 'r', encoding="utf-8") as json_file:
        all_data = json.load(json_file)

    with open('./data/all_actors.json', 'w', encoding="utf-8") as json_file:
        actor_json = make_actor_json(all_data)
        json.dump(actor_json, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
