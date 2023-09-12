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
        - txt/doc_type_mapping.json
    """
    __info_page_keywords: list[str] = []
    __stopwords: list[str] = []
    __labels: dict[str, Any]
    __doc_type_mapping: dict[str, str]
    __lang_labels: dict[str, Any] = {}
    __lang_doc_type_mapping: dict[str, Any] = {}

    @staticmethod
    def load(selected_languages: Optional[list[str]] = None) -> None:
        ResourceLoader.__load_info_page_keywords(selected_languages)
        ResourceLoader.__load_stopwords(selected_languages)
        ResourceLoader.__load_labels(selected_languages)
        ResourceLoader.__load_doc_type_mapping(selected_languages)

    @staticmethod
    def get_info_page_keywords() -> list[str]:
        return ResourceLoader.__info_page_keywords

    @staticmethod
    def get_stopwords() -> list[str]:
        return ResourceLoader.__stopwords

    @staticmethod
    def get_labels() -> dict[str, str]:
        return ResourceLoader.__labels

    @staticmethod
    def get_doc_type_mapping() -> dict[str, str]:
        return ResourceLoader.__doc_type_mapping

    @staticmethod
    def __load_info_page_keywords(selected_languages: Optional[list[str]] = None) -> None:
        if ResourceLoader.__info_page_keywords:
            return
        with files("metadata_extract.data").joinpath("txt/info_page_keywords.json").open() as file:
            keyword_data = json.load(file)
        for lang in keyword_data:
            if selected_languages is None or lang in selected_languages:
                ResourceLoader.__info_page_keywords.extend(keyword_data[lang])

    @staticmethod
    def __load_stopwords(selected_languages: Optional[list[str]] = None) -> None:
        if ResourceLoader.__stopwords:
            return
        with files("metadata_extract.data").joinpath("txt/stopwords.json").open() as file:
            stopwords_data = json.load(file)

        for lang in stopwords_data:
            if selected_languages is None or lang in selected_languages:
                ResourceLoader.__stopwords.extend(stopwords_data[lang])

    @staticmethod
    def __load_labels(selected_languages: Optional[list[str]] = None) -> None:
        if ResourceLoader.__lang_labels:
            return
        with files("metadata_extract.data").joinpath("txt/labels.json").open() as file:
            label_data = json.load(file)
        ResourceLoader.__lang_labels = {}
        if selected_languages:
            for lang in filter(lambda x: x in label_data, selected_languages):
                ResourceLoader.__lang_labels[lang] = label_data[lang]
        else:
            ResourceLoader.__lang_labels = label_data

        labels: dict[str, str] = {}
        for lang, label_dict in ResourceLoader.__lang_labels.items():
            for key in label_dict:
                if key not in labels:
                    labels[key] = ""
                labels[key] += "|" + "|".join(ResourceLoader.__lang_labels[lang][key])
        for key in labels:
            labels[key] = labels[key].lstrip("|").rstrip("|")
        ResourceLoader.__labels = labels

    @staticmethod
    def __load_doc_type_mapping(selected_languages: Optional[list[str]] = None) -> None:
        if ResourceLoader.__lang_doc_type_mapping:
            return
        with files("metadata_extract.data") \
                .joinpath("txt/doc_type_mapping.json").open() as file:
            ResourceLoader.__lang_doc_type_mapping = json.load(file)

        doc_type_mapping: dict[str, str] = {}
        if selected_languages:
            for lang in filter(
                    lambda x: x in ResourceLoader.__lang_doc_type_mapping, selected_languages
            ):
                doc_type_mapping.update(ResourceLoader.__lang_doc_type_mapping[lang])
        else:
            doc_type_mapping = ResourceLoader.__lang_doc_type_mapping
        ResourceLoader.__doc_type_mapping = doc_type_mapping
