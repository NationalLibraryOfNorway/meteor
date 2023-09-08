# pylint: disable=missing-module-docstring
import json
from importlib.resources import files
from typing import Any, Optional


class ResourceLoader:
    """ Class for loading resource files in the metadata_extract.data directory,
    which are applied to regular expressions in the metadata_extract.text module
    and in the keyword list of the metadata.infopage module.

    The application requires the following files used in this class to run:
        - txt/info_page_keywords.json
        - txt/stopwords.json
        - txt/labels.json
        - txt/doc_type_mapping_no_en.json
    """
    __info_page_keywords: list[str]
    __stopwords: list[str]
    __labels: dict[str, Any]
    __doc_type_mapping: dict[str, str]

    __lang_info_page_keywords: dict[str, list[str]]
    __lang_stopwords: dict[str, list[str]]
    __lang_labels: dict[str, Any]

    @staticmethod
    def load_info_page_keywords(selected_languages: Optional[list[str]] = None) -> None:
        with files("metadata_extract.data").joinpath("txt/info_page_keywords.json").open() as file:
            info_page_keywords = json.load(file)
            ResourceLoader.__lang_info_page_keywords = {}
            if selected_languages:
                for lang in filter(
                        lambda x: x in info_page_keywords, selected_languages
                ):
                    ResourceLoader.__lang_info_page_keywords[lang] = info_page_keywords[lang]
            else:
                ResourceLoader.__lang_info_page_keywords = info_page_keywords

    @staticmethod
    def load_stopwords(selected_languages: Optional[list[str]] = None) -> None:
        with files("metadata_extract.data").joinpath("txt/stopwords.json").open() as file:
            stopwords = json.load(file)
            ResourceLoader.__lang_stopwords = {}
            if selected_languages:
                for lang in filter(lambda x: x in stopwords, selected_languages):
                    ResourceLoader.__lang_stopwords[lang] = stopwords[lang]
            else:
                ResourceLoader.__lang_stopwords = stopwords

    @staticmethod
    def load_labels(selected_languages: Optional[list[str]] = None) -> None:
        with files("metadata_extract.data").joinpath("txt/labels.json").open() as file:
            labels = json.load(file)
            ResourceLoader.__lang_labels = {}
            if selected_languages:
                for lang in filter(lambda x: x in labels, selected_languages):
                    ResourceLoader.__lang_labels[lang] = labels[lang]
            else:
                ResourceLoader.__lang_labels = labels

    @staticmethod
    def get_info_page_keywords() -> list[str]:
        keywords = []
        for lang in ResourceLoader.__lang_info_page_keywords:
            keywords.extend(ResourceLoader.__lang_info_page_keywords[lang])
        ResourceLoader.__info_page_keywords = keywords
        return ResourceLoader.__info_page_keywords

    @staticmethod
    def get_stopwords() -> list[str]:
        stopwords = []
        for lang in ResourceLoader.__lang_stopwords:
            stopwords.extend(ResourceLoader.__lang_stopwords[lang])
        ResourceLoader.__stopwords = stopwords
        return ResourceLoader.__stopwords

    @staticmethod
    def get_labels() -> dict[str, str]:
        labels: dict[str, str] = {}
        for lang in ResourceLoader.__lang_labels:
            for key in ResourceLoader.__lang_labels[lang]:
                if key not in labels:
                    labels[key] = ""
                labels[key] += "|" + "|".join(ResourceLoader.__lang_labels[lang][key])
        for key in labels:
            labels[key] = labels[key].lstrip("|").rstrip("|")
        ResourceLoader.__labels = labels
        return ResourceLoader.__labels

    @staticmethod
    def get_doc_type_mapping() -> dict[str, str]:
        with files("metadata_extract.data") \
                .joinpath("txt/doc_type_mapping_no_en.json").open() as file:
            ResourceLoader.__doc_type_mapping = json.load(file)
        return ResourceLoader.__doc_type_mapping
