"""Test the output from Meteor.run on a sample PDF file"""


from metadata_extract.meteor import Meteor


meteor = Meteor()
results = meteor.run('test/resources/report1.pdf')


def test_year():
    assert results['year'] == {
        "value": 2021,
        "origin": {
            "type": "COPYRIGHT",
            "pageNumber": 4
        }
    }


def test_language():
    assert results['language'] == {
        "value": "nb",
        "origin": {
            "type": "LANGUAGE_MODEL"
        }
    }


def test_title():
    assert results['title'] == {
        "value": "Barnefaglig kompetanse i utlendingsforvaltningen",
        "origin": {
            "type": "PDFINFO",
            "pageNumber": 1
        }
    }


def test_publisher():
    assert results['publisher'] == {
        "value": "Fafo",
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
            "firstname": "Ragna",
            "lastname": "Lillevik",
            "origin": {
                "type": "FRONT_PAGE"
            }
        },
        {
            "firstname": "Lene Christin",
            "lastname": "Holum",
            "origin": {
                "type": "FRONT_PAGE"
            }
        },
        {
            "firstname": "Nerina",
            "lastname": "Weiss",
            "origin": {
                "type": "FRONT_PAGE"
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
        "value": "978-82-324-0629-6",
        "origin": {
            "type": "PAGE",
            "pageNumber": 4
        }
    }


def test_issn():
    assert results['issn'] == {
        "value": "2387-6859",
        "origin": {
            "type": "PAGE",
            "pageNumber": 4
        }
    }
