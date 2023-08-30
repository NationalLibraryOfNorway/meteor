"""Test InfoPage methods, using a sample PDF file"""


from metadata_extract.infopage import InfoPage
from metadata_extract.meteor_document import MeteorDocument

doc = MeteorDocument('test/resources/report2.pdf')
infopagenr = InfoPage.find_page_number(doc.pages)


def test_infopagenr():
    assert infopagenr == 2


test_infopage = InfoPage(doc.document, infopagenr)
doc.close()


def test_find_title():
    expected_title = 'Muligheter og utfordringer for økt karbonbinding i jordbruksjord'
    assert test_infopage.find_title() == expected_title


def test_find_isxn():
    isbn = test_infopage.find_isxn('ISBN')
    assert isbn[0].value == '978-82-17-02298-5'
    issn = test_infopage.find_isxn('ISSN')
    assert issn[0].value == '2464-1162'


def test_find_authors():
    authors = test_infopage.find_author()
    assert set(authors) == {'Daniel Rasse', 'Inghild Økland', 'Teresa G. Bárcena',
                            'Hugh Riley', 'Vegard Martinsen', 'Ievina Sturite'}
