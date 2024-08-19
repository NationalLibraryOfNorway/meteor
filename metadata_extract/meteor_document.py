"""MeteorDocument module

Serves as an interface between the file on disk and the internal object used in Meteor.
"""


import json
from pathlib import Path
import re
from types import TracebackType
from typing import Optional, Self, Type
import fitz
import regex
from .page import Page
from .alto_utils import AltoFile


class MeteorDocument:
    """This class represents the internal object on which Meteor heuristics are run.

    It is responsible for loading the file from disk and offers methods to load its
    content. MeteorDocuments are context managers, so they can be used in `with` statements.
    """

    # text extraction settings for LLM
    PAGES = [0, 1, 2, 3, 4, 5, 6, 7, -2, -1]  # pages to analyze: first 8 pages + last 2 pages
    THRESHOLD = 100                       # paragraphs shorter than this will always be kept
    LONG_PARA_PAGES = [0, 1]         # on first two pages, some long paragraphs are accepted
    LONG_PARA_MAX = 2                # how many long paragraphs to keep on the first two pages
    PDF_METADATA_SKIP = {'format', 'creator', 'producer'}  # PDF metadata fields not to include

    def __init__(self, file_path: str,
                 start: int = 5,
                 end: int = 5):
        path = Path(file_path)
        self.pdfinfo: Optional[dict[str, str]] = None
        self.pdfdoc: Optional[fitz.Document] = None
        if path.is_dir():
            # TODO: handle errors
            self.pages, self.page_objects = self.__read_alto_pages(path, start, end)
        elif path.is_file():
            self.pdfdoc = fitz.open(file_path)
            self.pdfinfo = self.pdfdoc.metadata
            self.pages = self.__read_pdf_pages(start, end)
            self.page_objects = {}
        else:
            raise ValueError('bad argument')

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        self.close()

    def close(self) -> None:
        if self.pdfdoc:
            self.pdfdoc.close()

    def __read_pdf_pages(self, start: int, end: int) -> dict[int, str]:
        """Builds a dictionary associating page number to a string containing each page's text."""
        if not self.pdfdoc:
            raise ValueError('No PDF document set')
        pages = {}
        if self.pdfdoc.page_count < start + end:
            for page in range(self.pdfdoc.page_count):
                pages[page+1] = self.pdfdoc.get_page_text(page)
        else:
            for page in range(start):
                pages[page+1] = self.pdfdoc.get_page_text(page)
            for page in range(self.pdfdoc.page_count-end, self.pdfdoc.page_count):
                pages[page+1] = self.pdfdoc.get_page_text(page)
        return pages

    def __read_alto_pages(self, path: Path, start: int, end: int
                          ) -> tuple[dict[int, str], dict[int, Page]]:
        """Builds a dictionary associating page number to a string containing each page's text."""
        pages_txt = {}
        pages_objects = {}
        alto_files = sorted(path.glob('*.xml'))

        files_to_read = []
        if len(alto_files) < start + end:
            files_to_read = alto_files
        else:
            files_to_read = alto_files[:start]
            files_to_read.extend(alto_files[-end:])

        for alto_file in files_to_read:
            page_nr = int(alto_file.name.split('.')[0][-4:])
            alto = AltoFile(alto_file)
            pages_txt[page_nr] = alto.full_text
            pages_objects[page_nr] = Page(alto_file=alto)

        return pages_txt, pages_objects

    def get_page_object(self, page_number: int) -> Page:
        """Builds a Page object for page_number, and caches it in the page_objects attribute."""
        if page_number not in self.page_objects:
            if not self.pdfdoc:
                raise ValueError('No PDF file to load page from')
            self.page_objects[page_number] = Page(pdf_page=self.pdfdoc.load_page(page_number - 1))
        return self.page_objects[page_number]

    def extract_text_as_json(self) -> str:
        """Extract text and metadata as a JSON string suitable for a LLM"""

        if not self.pdfdoc:
            raise ValueError('No PDF document set')

        pdfinfo = {}
        pages = []

        for key in self.pdfdoc.metadata.keys():
            if key not in self.PDF_METADATA_SKIP and self.pdfdoc.metadata.get(key):
                pdfinfo[key] = self.pdfdoc.metadata.get(key)

        for page in self.PAGES:
            if page > len(self.pdfdoc) - 2:
                continue

            texts = []
            text = self.pdfdoc[page].get_text(sort=True)
            # Use regular expression to split text into paragraphs
            # Delimiter: newline(s) followed by an upper case character
            paragraphs = regex.split(r'\n+(?=\p{Lu})', text, flags=re.UNICODE)
            long_paragraph_count = 0

            for paragraph in paragraphs:
                paragraph = " ".join(paragraph.strip().split())

                if '.....' in paragraph or '. . . . .' in paragraph:
                    # looks like a ToC entry, skip it
                    continue
                if len(paragraph) < self.THRESHOLD:  # short paragraph, keep it
                    texts.append(paragraph)
                elif page in self.LONG_PARA_PAGES and long_paragraph_count < self.LONG_PARA_MAX:
                    # allow some long paragraphs on the first two pages
                    long_paragraph_count += 1
                    texts.append(paragraph)
                else:  # must be a long paragraph, skip it
                    pass
            text = '\n'.join(texts)
            if text:
                pages.append({"page": self.pdfdoc[page].number, "text": text})

        return json.dumps({"pdfinfo": pdfinfo, "pages": pages})
