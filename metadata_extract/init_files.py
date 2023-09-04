# pylint: disable=missing-module-docstring
import json
from importlib.resources import files
from typing import Type, Any

from src.settings import get_settings


class InitFiles:
    """ Class for loading the files in the metadata_extract.data directory,
    which are applied to regular expressions in the metadata_extract.text module
    and in the keyword list of the metadata.infopage module.

    The class is implemented as a singleton, so that the files are only read once.

    The application requires the following files used in this class to run:
        - txt/info_page_keywords.json
        - txt/stopwords.json
        - txt/labels.json
        - txt/doc_type_mapping_no_en.json
    """
    _instance = None
    _initialized = False

    def __new__(cls: Type['InitFiles'], *args: Any, **kwargs: Any) -> 'InitFiles':
        if not cls._instance:
            cls._instance = super(InitFiles, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        if InitFiles._initialized:
            return
        self.languages = get_settings().LANGUAGES.split(',')
        self.info_page_keywords = self.__init_info_page_keywords()
        self.stopwords = self.__init_stopwords()
        self.labels = self.__init_labels()
        self.doc_type_mapping = self.__init_doc_type_mapping()
        InitFiles._initialized = True

    @staticmethod
    def get_info_page_keywords() -> list[str]:
        return InitFiles().info_page_keywords

    @staticmethod
    def get_stopwords() -> list[str]:
        return InitFiles().stopwords

    @staticmethod
    def get_labels() -> dict[str, str]:
        return InitFiles().labels

    @staticmethod
    def get_doc_type_mapping() -> dict[str, str]:
        return InitFiles().doc_type_mapping

    def __init_info_page_keywords(self) -> list[str]:
        keywords = []
        with files("metadata_extract.data").joinpath("txt/info_page_keywords.json").open() as file:
            languages = json.load(file)
            [keywords.extend(languages[lang]) for lang in self.languages if lang in languages]
        return keywords

    def __init_stopwords(self) -> list[str]:
        stopwords = []
        with files("metadata_extract.data").joinpath("txt/stopwords.json").open() as file:
            languages = json.load(file)
            [stopwords.extend(languages[lang]) for lang in self.languages if lang in languages]
        return stopwords

    def __init_labels(self) -> dict[str, str]:
        labels = {}
        with files("metadata_extract.data").joinpath("txt/labels.json").open() as file:
            languages = json.load(file)
            [self.__get_labels_from_lang(labels, lang, languages) for lang in self.languages if lang in languages]
        for key in labels:
            labels[key] = labels[key].lstrip("|").rstrip("|")
        return labels

    def __get_labels_from_lang(self, labels: dict, lang, languages) -> None:
        for key in languages[lang]:
            if key not in labels:
                labels[key] = ""
            labels[key] += "|" + "|".join(languages[lang][key])

    def __init_doc_type_mapping(self) -> dict[str, str]:
        doc_type_mapping = {}
        with files("metadata_extract.data")\
                .joinpath("txt/doc_type_mapping_no_en.json").open() as file:
            doc_type_mapping = json.load(file)
        return doc_type_mapping
