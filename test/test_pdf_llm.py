# pylint: disable=R0801

"""Test the output from Meteor.run on a sample PDF file using LLM extraction"""


import json
import unittest.mock
from metadata_extract.meteor import Meteor


meteor = Meteor()
meteor.set_llm_config({
    'api_url': 'http://localhost:8080/',
    'api_key': '',
    'model': ''
})

# set up mock LLM response that will be used instead of a real LLM
with open('test/resources/pdf_report_llm_response.json', encoding='utf-8') as response_file:
    mock_llm_response = json.load(response_file)

with unittest.mock.patch("requests.post") as mock_request:
    # create a mock response whose .json() method returns the list that we define here
    mock_response = unittest.mock.Mock()
    mock_response.json.return_value = mock_llm_response
    mock_request.return_value = mock_response

    # run Meteor, triggering the call to the LLM
    results = meteor.run('test/resources/report.pdf', backend='LLMExtractor')


def test_year():
    assert results['year'] == {
        "value": 2023,
        "origin": {
            "type": "LLM"
        }
    }


def test_language():
    assert results['language'] == {
        "value": "no",
        "origin": {
            "type": "LLM"
        }
    }


def test_title():
    assert results['title'] == {
        "value": "Metadataekstrahering – Muligheter og innsikt",
        "origin": {
            "type": "LLM"
        }
    }


def test_publisher():
    assert results['publisher'] == {
        "value": "Nasjonalbiblioteket",
        "origin": {
            "type": "LLM"
        }
    }


def test_authors():
    expected_dict = [
        {
            "firstname": "Bjørnstjerne M.",
            "lastname": "Bjørnson",
            "origin": {
                "type": "LLM"
            }
        },
        {
            "firstname": "Jacobine",
            "lastname": "Camilla-Collett",
            "origin": {
                "type": "LLM"
            }
        },
        {
            "firstname": "Henrik J.",
            "lastname": "Ibsen",
            "origin": {
                "type": "LLM"
            }
        },
        {
            "firstname": "Raymond",
            "lastname": "McArthur",
            "origin": {
                "type": "LLM"
            }
        },
        {
            "firstname": "John",
            "lastname": "O’Toole",
            "origin": {
                "type": "LLM"
            }
        }
    ]

    all_expected_authors_found = True
    for author in results['authors']:
        if author in expected_dict:
            expected_dict.remove(author)
        else:
            all_expected_authors_found = False
            break

    assert len(expected_dict) == 0 and all_expected_authors_found


def test_isbn():
    assert results['isbn'] == {
        "value": "9788217022985",
        "origin": {
            "type": "LLM"
        }
    }


def test_issn():
    assert results['issn'] == {
        "value": "2464-1162",
        "origin": {
            "type": "LLM"
        }
    }
