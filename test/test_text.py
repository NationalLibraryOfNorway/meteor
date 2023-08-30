"""Test methods from the text module"""


from metadata_extract import text


def test_title_search_with_perfect_match():
    title = "A possible title from pdfinfo"
    pages = {1: "02/2023 Report \n\nA possible title from pdfinfo\n\nwith an undertitle"}
    found = text.find_in_pages(title, pages)
    assert found == 1


def test_title_search_should_allow_for_nonalphanum_char():
    title = "A possible title from pdfinfo"
    pages = {1: "02/2023 Report \n\nA possible title:\nfrom-\npdfinfo\n\nwith an undertitle"}
    found = text.find_in_pages(title, pages)
    assert found == 1


def test_title_search_should_fail_if_not_matching_word_boundaries():
    title = "A possible title from pdfinfo"
    pages = {1: "02/2023 Report \n\nA possible title from pdfinformation"}
    found = text.find_in_pages(title, pages, max_pages=1)
    assert found == 0


def test_title_search_should_fail_if_unmatched_alphanum_inside():
    title = "Å possible title from pdfinfo"
    pages = {1: "02/2023 Report \n\nÅ possible title from what we got in pdfinfo"}
    found = text.find_in_pages(title, pages, max_pages=1)
    assert found == 0


def test_report_prefix_search():
    assert text.find_report_prefix('NAV-report') == 'NAV'
    assert text.find_report_prefix('NIBIO RAPPORT  |  VOL. 3  |  NR. 45') == 'NIBIO'
    assert text.find_report_prefix('FHI') is None
    assert text.find_report_prefix('This FHI report') is None
    assert text.find_report_prefix('ÅRSRAPPORT') is None


def test_no_letters():
    assert text.has_no_letters('2020/02') is True
    assert text.has_no_letters('2020/02 Report from') is False
