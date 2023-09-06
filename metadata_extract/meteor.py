"""Main module for Meteor"""


from .resource_loader import ResourceLoader
from typing import Optional, Callable
import langdetect
from langdetect.lang_detect_exception import LangDetectException
from .registry import PublisherRegistry
from .meteor_document import MeteorDocument
from .metadata import Results
from .finder import Finder


class Meteor:
    """A Meteor object is the entrypoint for the package.

    External resources needed: SQLite database for name registry, and directory for
    language models.
    The `run` method will create a MeteorDocument, find candidate values for metadata
    and return the best ones as a Results object (TypedDict, JSON-serializable)
    """

    def __init__(self, languages: Optional[list[str]] = None) -> None:
        self.registry: Optional[PublisherRegistry] = None
        ResourceLoader.load(languages)
        self.detect_language: Callable[[str], Optional[str]] = Meteor.__default_detect

    @staticmethod
    def __default_detect(text: str) -> Optional[str]:
        try:
            lang = langdetect.detect(text)
        except LangDetectException:
            return None
        if not isinstance(lang, str) or lang == "unknown":
            return None
        return lang

    def set_registry(self, registry: PublisherRegistry) -> None:
        self.registry = registry

    def set_language_detection_method(self, detect_language: Callable[[str], str]) -> None:
        self.detect_language = detect_language

    def run(self, file_path: str) -> Results:
        with MeteorDocument(file_path) as doc:
            finder = Finder(doc, self.registry, self.detect_language)
            finder.extract_metadata()
            finder.metadata.choose_best()
            return finder.metadata.results
