import pytest

import movie_scraper


@pytest.mark.parametrize(
    "test_input,expected", [
        ("Raymond Blathwayt – Sir Hugh", "Raymond Blathwayt")  # important to test em-dash vs en-dash
    ]
)
def test_clean_actor(test_input, expected):
    assert movie_scraper.clean_actor(test_input) == expected
