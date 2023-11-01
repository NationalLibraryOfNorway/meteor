"""Test the output from Meteor.run on a sample PDF file"""


from metadata_extract.meteor import Meteor


meteor = Meteor()
results = meteor.run('test/resources/report.pdf')


def test_year():
    assert results['year'] == {
        "value": 2023,
        "origin": {
            "type": "COPYRIGHT",
            "pageNumber": 4
        }
    }


def test_language():
    assert results['language'] == {
        "value": "no",
        "origin": {
            "type": "LANGUAGE_MODEL"
        }
    }


def test_title():
    assert results['title'] == {
        "value": "Metadataekstrahering – Muligheter og innsikt",
        "origin": {
            "type": "FRONT_PAGE"
        }
    }


def test_publisher():
    assert results['publisher'] == {
        "value": "Nasjonalbiblioteket",
        "origin": {
            "type": "COPYRIGHT",
            "pageNumber": 4
        }
    }


def test_publication_type():
    assert results['publicationType'] == {
        "value": "evaluation",
        "origin": {
            "type": "FRONT_PAGE"
        }
    }


def test_authors():
    expected_dict = [
        {
            "firstname": "Bjørnstjerne M.",
            "lastname": "Bjørnson",
            "origin": {
                "type": "INFO_PAGE",
                "pageNumber": 2
            }
        },
        {
            "firstname": "Jacobine",
            "lastname": "Camilla-Collett",
            "origin": {
                "type": "INFO_PAGE",
                "pageNumber": 2
            }
        },
        {
            "firstname": "Henrik J.",
            "lastname": "Ibsen",
            "origin": {
                "type": "INFO_PAGE",
                "pageNumber": 2
            }
        },
        {
            "firstname": "Raymond",
            "lastname": "McArthur",
            "origin": {
                "type": "INFO_PAGE",
                "pageNumber": 2
            }
        },
        {
            "firstname": "John",
            "lastname": "O’Toole",
            "origin": {
                "type": "INFO_PAGE",
                "pageNumber": 2
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
            "type": "PAGE",
            "pageNumber": 2
        }
    }


def test_issn():
    assert results['issn'] == {
        "value": "2464-1162",
        "origin": {
            "type": "PAGE",
            "pageNumber": 2
        }
    }
