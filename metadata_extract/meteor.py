"""Main module for Meteor"""


from importlib.resources import files
from typing import Optional
from language.pytextcat import Classifier
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

    def __init__(self, lm_dir: str = str(files('language.data').joinpath('lm'))):
        self.registry: Optional[PublisherRegistry] = None
        self.classifier = Classifier(folder=lm_dir)

    def set_registry(self, registry: PublisherRegistry) -> None:
        self.registry = registry

    def run(self, file_path: str) -> Results:
        with MeteorDocument(file_path) as doc:
            finder = Finder(doc, self.registry, self.classifier)
            finder.extract_metadata()
            finder.metadata.choose_best()
            return finder.metadata.results
