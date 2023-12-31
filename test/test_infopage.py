"""Test Page and InfoPage methods, using a sample PDF file"""


from metadata_extract.infopage import InfoPage
from metadata_extract.meteor_document import MeteorDocument
from metadata_extract.resource_loader import ResourceLoader

doc = MeteorDocument('test/resources/report.pdf')
ResourceLoader.load(["mul", "eng", "nob", "nno"])
infopagenr = InfoPage.find_page_number(doc.pages)


def test_infopagenr():
    assert infopagenr == 2


page_object = doc.get_page_object(infopagenr)
test_infopage = InfoPage(page_object)


def test_find_title():
    expected_title = 'Metadataekstrahering – Muligheter og innsikt'
    assert test_infopage.find_title() == expected_title


def test_find_isxn():
    isbn = page_object.find_isxn('ISBN')
    assert isbn[0].value == '978-82-17-02298-5'
    issn = page_object.find_isxn('ISSN')
    assert issn[0].value == '2464-1162'


def test_find_authors():
    authors = test_infopage.find_author()
    assert set(authors) == {'Bjørnstjerne M. Bjørnson', 'Jacobine Camilla-Collett',
                            'Henrik J. Ibsen', 'Raymond McArthur', 'John O’Toole'}


doc.close()
