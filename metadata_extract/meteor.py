"""Main module for Meteor"""


from typing import Optional

from .resource_loader import ResourceLoader
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

    def set_registry(self, registry: PublisherRegistry) -> None:
        self.registry = registry

    def run(self, file_path: str) -> Results:
        with MeteorDocument(file_path) as doc:
            finder = Finder(doc, self.registry)
            finder.extract_metadata()
            finder.metadata.choose_best()
            return finder.metadata.results
