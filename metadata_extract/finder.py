"""The finder module is where the actual heuristics are implemented."""


# pylint: disable=broad-exception-caught

import traceback
from typing import TypedDict, NotRequired, Optional
from dateutil.parser import parse
from dateparser.search import search_dates
import langdetect
from langdetect.lang_detect_exception import LangDetectException
from . import text, author_name
from .candidate import Candidate, Origin
from .infopage import InfoPage
from .metadata import Metadata
from .meteor_document import MeteorDocument
from .registry import PublisherRegistry, RegistryType


class CopyrightType(TypedDict):
    """Contains fields parsed from a copyright line."""
    publisher: str
    year: NotRequired[int]


class Finder:
    """A finder object loads a MeteorDocument and fills a Metadata object.

    The only method called from outside is finder.extract_metadata, which calls
    all the inner methods in a defined order.
    """

    def __init__(self, doc: MeteorDocument,
                 registry: Optional[PublisherRegistry]):
        self.doc = doc
        self.registry = registry
        self.metadata = Metadata()

    def search_in_registry(self, name: str) -> list[RegistryType]:
        if not self.registry:
            return []
        try:
            return self.registry.search(name)
        except Exception:
            print(traceback.format_exc())
            return []

    def find_report_prefix(self) -> None:
        """Looks in all pages for mention of publisher in the format <name>-report."""
        for pagenumber in self.doc.pages:
            page = self.doc.document.load_page(pagenumber - 1)
            blocks = page.get_text("blocks")
            for block in blocks:
                if block[-1] == 1:  # image block
                    continue
                line = block[4].split('\n')[0].strip()  # only use first line of block
                if text.has_no_letters(line) or len(line) == 1:
                    continue
                if self.metadata.has_publisher(line):
                    continue
                report_prefix = text.find_report_prefix(line)
                if report_prefix:
                    if self.metadata.has_publisher(report_prefix):
                        continue
                    publisher = Candidate(report_prefix, Origin.RAPPORT_PREFIX, page_nr=pagenumber)
                    publisher.reg_entries = self.search_in_registry(report_prefix)
                    self.metadata.add_candidate('publisher', publisher)

    def find_title_from_page(self) -> None:
        """Looks for the block on the first page using the largest font and containing letters,
        and adds its text value as a title candidate."""
        page = self.doc.get_page_object(1)
        blocks: dict[float, list[str]] = {}
        for block in page.text_blocks:
            if block.fontsize not in blocks:
                blocks[block.fontsize] = []
            blocks[block.fontsize].append(block.text)
        sorted_dict = sorted(blocks.items(), key=lambda x: -x[0])
        for block_by_font in sorted_dict:
            block_text = ' '.join(block_by_font[1])
            if not text.has_no_letters(block_text):
                title_value = text.clean_whitespace(block_text)
                self.metadata.add_candidate('title', Candidate(title_value, Origin.FRONT_PAGE))
                return

    def find_isxn(self, identifier: str) -> None:
        """Looks for ISXN numbers in all pages."""
        for number, page in self.doc.pages.items():
            if identifier not in page:
                continue
            page_object = self.doc.get_page_object(number)
            isxn_values = page_object.find_isxn(identifier)
            for isxn_value in isxn_values:
                candidate = Candidate(isxn_value.value, Origin.PAGE,
                                      page_nr=number, context=isxn_value.context)
                self.metadata.add_candidate(identifier, candidate)

    def find_publisher(self) -> None:
        """Looks in all pages for a publisher label, and adds associated value as a candidate.
        Returns after first value is found."""
        for number, page in self.doc.pages.items():
            for line in page.split('\n'):
                match = text.PUBLISHER_LABEL.match(line)
                if match is not None:
                    value = line[match.span()[1]:].strip()
                    if value != '':
                        publisher = Candidate(value, Origin.PAGE, page_nr=number)
                        publisher.reg_entries = self.search_in_registry(value)
                        self.metadata.add_candidate('publisher', publisher)
                    elif not self.metadata.has_publisher_from_infopage():
                        page_object = self.doc.get_page_object(number)
                        publisher_block = page_object.find_publisher()
                        if publisher_block:
                            publisher = Candidate(publisher_block, Origin.PAGE, page_nr=number)
                            publisher.reg_entries = self.search_in_registry(publisher_block)
                            self.metadata.add_candidate('publisher', publisher)
                    return

    def find_author(self) -> None:
        """Looks for authors names in text blocks of all pages."""
        front_page_text = self.doc.get_page_object(1).text_blocks
        block_to_str = author_name.concat_text_blocks_to_str(front_page_text)
        authors = author_name.get_author_names(block_to_str)

        if not authors:
            return

        found_title = None
        if 'title' in self.metadata.candidates:
            found_title = self.metadata.candidates["title"][0].value

        for author in authors:
            # TODO: avoid typecheck
            if found_title and isinstance(found_title, str) \
               and author_name.name_exists_in_title(found_title, author):
                continue
            if any(keyword in author.lower() for keyword in text.STOPWORDS):
                continue
            if author_name.is_all_caps_spaced(author):
                continue
            candidate = Candidate(author_name.create_author_dict(author), Origin.FRONT_PAGE)
            self.metadata.add_candidate('author', candidate)

    def parse_copyright(self) -> None:
        """Looks for a © symbol in all pages, then parses it as publisher name and year."""
        for number, page in self.doc.pages.items():
            for line in page.split('\n'):
                if '©' in line:
                    clean_line = text.clean_whitespace(line[line.index('©')+1:])
                    result = self.parse_copyright_line(clean_line)
                    if 'year' in result:
                        candidate = Candidate(result['year'], Origin.COPYRIGHT, page_nr=number)
                        self.metadata.add_candidate('year', candidate)
                    if result['publisher'] and not self.metadata.has_publisher(result['publisher']):
                        publisher = Candidate(result['publisher'], Origin.COPYRIGHT,
                                              page_nr=number)
                        publisher.reg_entries = self.search_in_registry(result['publisher'])
                        self.metadata.add_candidate('publisher', publisher)

    def parse_copyright_line(self, copyright_line: str) -> CopyrightType:
        """Parses the ©-string as publisher name and year."""
        result: CopyrightType = {'publisher': ''}
        found_date = search_dates(copyright_line, settings={'REQUIRE_PARTS': ['year']})
        if found_date is None:
            result['publisher'] = copyright_line.replace('©', '').strip(' .,')
        else:
            result['year'] = found_date[0][1].year
            index = copyright_line.find(found_date[0][0])
            if index < 0:
                result['publisher'] = copyright_line.replace('©', '').strip(' .,')
            else:
                result['publisher'] = copyright_line[:index].replace('©', '').strip(' .,')
        return result

    def get_title_from_info(self) -> None:
        """If the title value in PDF info is also found in the document's text (allowing for
        small edits), adds it as a title candidate."""
        if self.doc.pdfinfo['title']:
            title = self.doc.pdfinfo['title']
            found_on_page = text.find_in_pages(title, self.doc.pages)
            if found_on_page > 0:
                candidate = Candidate(self.doc.pdfinfo['title'], Origin.PDFINFO,
                                      page_nr=found_on_page)
                self.metadata.add_candidate('title', candidate)

    def get_author_from_info(self) -> None:
        """If the author value in PDF info is also found in the document's text (allowing for
        small edits), adds it as an author candidate."""
        # TODO: Seems to only fetch first author before comma from pdfinfo
        if self.doc.pdfinfo['author']:
            author = self.doc.pdfinfo['author']
            name_match = text.NAME_PATTERN.findall(author)
            for match in name_match:
                found_on_page = text.find_in_pages(match, self.doc.pages)
                if any(keyword in author.lower() for keyword in text.STOPWORDS):
                    continue
                if found_on_page > 0:
                    candidate = Candidate(author_name.create_author_dict(match),
                                          Origin.PDFINFO, page_nr=found_on_page)
                    self.metadata.add_candidate('author', candidate)

    def get_year_from_info(self) -> None:
        """Adds the PDF info modDate, or creationDate, as a candidate if it can be found in text."""
        year = None
        if self.doc.pdfinfo['modDate']:
            year = parse(self.doc.pdfinfo['modDate'][2:14]).year
        elif self.doc.pdfinfo['creationDate']:
            year = parse(self.doc.pdfinfo['creationDate'][2:14]).year
        if year is None:
            return
        found_on_page = 0
        for number, page in self.doc.pages.items():
            if str(year) in page:
                found_on_page = number
                break
        if found_on_page > 0:
            candidate = Candidate(year, Origin.PDFINFO, page_nr=found_on_page)
            self.metadata.add_candidate('year', candidate)

    def get_language(self) -> None:
        """Detects language of concatenated text, and adds it as a candidate."""
        try:
            lang = langdetect.detect(' '.join(self.doc.pages.values()))
            self.metadata.add_candidate('language', Candidate(lang, Origin.LANGUAGE_MODEL))
        except LangDetectException:
            return

    def read_info_page(self) -> None:
        """Finds the infopage and searches for candidate values for title, publisher and authors."""
        infopagenr = InfoPage.find_page_number(self.doc.pages)
        if not infopagenr:
            return
        infopage = InfoPage(self.doc.document, infopagenr)
        title = infopage.find_title()
        if title:
            candidate = Candidate(title, Origin.INFO_PAGE, page_nr=infopagenr)
            self.metadata.add_candidate('title', candidate)
        publisher = infopage.find_publisher()
        if publisher:
            cand = Candidate(publisher, Origin.INFO_PAGE, page_nr=infopagenr)
            cand.reg_entries = self.search_in_registry(publisher)
            self.metadata.add_candidate('publisher', cand)
        author_list = infopage.find_author()
        if author_list:
            for author in author_list:
                candidate = Candidate(author_name.create_author_dict(author),
                                      Origin.INFO_PAGE, page_nr=infopagenr)
                self.metadata.add_candidate('author', candidate)

    def find_document_type(self) -> None:
        """Tries to identify the document type using the first page's text."""
        doc_type = text.find_doc_type(self.doc.pages[1])
        if doc_type:
            self.metadata.add_candidate('document_type', Candidate(doc_type, Origin.FRONT_PAGE))

    def extract_metadata(self) -> None:
        """Calls all methods to add candidates to the Metatdata attribute.

        Note: The calling order matters. For example find_author uses the title candidates, so
        title-related methods have to be called beforehand.
        """
        self.find_title_from_page()
        self.get_title_from_info()
        self.get_author_from_info()
        self.get_year_from_info()
        self.find_isxn('ISBN')
        self.find_isxn('ISSN')
        self.read_info_page()
        self.find_publisher()
        self.parse_copyright()
        self.find_report_prefix()
        self.get_language()
        self.find_author()
        self.find_document_type()
