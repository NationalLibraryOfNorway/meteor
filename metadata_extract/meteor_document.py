"""MeteorDocument module

Serves as an interface between the file on disk and the internal object used in Meteor.
"""


from types import TracebackType
from typing import Optional, Self, Type
import fitz
from .page import Page


class MeteorDocument:
    """This class represents the internal object on which Meteor heuristics are run.

    It is responsible for loading the file from disk and offers methods to load its
    content. MeteorDocuments are context managers, so they can be used in `with` statements.
    """

    def __init__(self, file_path: str,
                 start: int = 5,
                 end: int = 5):
        self.document = fitz.open(file_path)
        self.pdfinfo = self.document.metadata
        self.pages = self.__read_pages(start, end)
        self.page_objects: dict[int, Page] = {}

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        self.close()

    def close(self) -> None:
        self.document.close()

    def __read_pages(self, start: int, end: int) -> dict[int, str]:
        """Builds a dictionary associating page number to a string containing each page's text."""
        pages = {}
        if self.document.page_count < start + end:
            for page in range(self.document.page_count):
                pages[page+1] = self.document.get_page_text(page)
        else:
            for page in range(start):
                pages[page+1] = self.document.get_page_text(page)
            for page in range(self.document.page_count-end, self.document.page_count):
                pages[page+1] = self.document.get_page_text(page)
        return pages

    def get_page_object(self, page_number: int) -> Page:
        """Builds a Page object for page_number, and caches it in the page_objects attribute."""
        if page_number not in self.page_objects:
            self.page_objects[page_number] = Page(self.document, page_number)
        return self.page_objects[page_number]
