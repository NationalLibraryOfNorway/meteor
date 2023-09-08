"""Text module, containing methods and logic dealing with strings and regexes."""

import re
from typing import Optional, Pattern

import regex

from metadata_extract.resource_loader import ResourceLoader


class ValueAndContext:
    """Stores a text value with surrounding context"""
    def __init__(self, value: str, context: Optional[str] = None):
        self.value = value
        self.context = context

    def append_to_context(self, extra_context: str) -> None:
        self.context = (self.context or '') + extra_context


def labels() -> dict[str, str]:
    return ResourceLoader.get_labels()


def stopwords() -> list[str]:
    return ResourceLoader.get_stopwords()


def info_page_keywords() -> list[str]:
    return ResourceLoader.get_info_page_keywords()


ISXN_PATTERN = {
    'ISSN': re.compile(r"\D(\d{4}[–-][\dX]{4})\D"),
    'ISBN': re.compile(r"\D([\d–-]{13,17})\D")
}


def report_pattern() -> Pattern[str]:
    return re.compile(fr'^(\w+)\W({labels()["report"]})\W', re.IGNORECASE)


def type_pattern_1() -> Pattern[str]:
    return re.compile(fr'\b({labels()["reportType"]})\b', re.IGNORECASE)


def type_pattern_2() -> Pattern[str]:
    return re.compile(r'\bNOU\b')


def doc_type_mapping() -> dict[str, str]:
    return ResourceLoader.get_doc_type_mapping()


def publisher_label() -> Pattern[str]:
    return re.compile(fr'({labels()["publisher"]}):?', re.IGNORECASE)


def no_letters_pattern() -> Pattern[str]:
    return re.compile(r'^[\W\d]+$')


def author_label() -> Pattern[str]:
    return re.compile(fr'({labels()["author"]}):?', re.IGNORECASE)


def name_pattern() -> regex.regex.Pattern[str]:
    return regex.compile(r"\b[^\P{Lu}][^\P{Ll}]*[-|‐]?[^\P{Lu}]?[^\P{Ll}’]*\.?" +
                         r"(?: [^\P{Lu}][^\P{Ll}’]*[-|‐]?[^\P{Lu}]?[^\P{Ll}]*\.?)+\b(?! *\()")


def parenthesis_pattern() -> Pattern[str]:
    return re.compile(r"\(.*?\)")


def double_capital_letter_pattern() -> Pattern[str]:
    return re.compile(r"\b[A-Z]{2,}\b")


def binding_word_pattern() -> Pattern[str]:
    return re.compile(fr'\b(?:{labels()["bindingWords"]})\b|&|,')


def special_char_and_binding_pattern() -> Pattern[str]:
    return re.compile(fr'[;:,.]|({labels()["bindingWords"]})\b|&+')


def non_alphanumeric_pattern() -> Pattern[str]:
    return re.compile(r"\W+")


def photograph_label() -> Pattern[str]:
    return re.compile(fr'\b({labels()["photo"]})\b', re.IGNORECASE)


def find_in_pages(title: str, pages: dict[int, str], max_pages: int = 3) -> int:
    """Tries to find the <title> argument in the pages dictionary.

    Optional argument to stop the search after <max_pages> pages.
    Returns page number (starts at 1) if the title is found or 0 otherwise."""
    title_tokens = re.sub(r'\W+', ' ', title).strip()
    for page_number in range(min(len(pages), max_pages)):
        page_tokens = re.sub(r'\W+', ' ', pages[page_number + 1]).strip()
        if f' {title_tokens} ' in f' {page_tokens} ':
            return page_number + 1
    return 0


def find_isxn(identifier: str, text: str) -> Optional[ValueAndContext]:
    match = ISXN_PATTERN[identifier].search("." + text + ".")
    if match:
        return ValueAndContext(re.sub('–', '-', match.group(1)), text.lower())
    return None


def find_report_prefix(text: str) -> Optional[str]:
    match = report_pattern().search(text + '.')
    if match:
        prefix = match.group(1)
        if prefix.isupper():
            return prefix
    return None


def find_doc_type(page_text: str) -> Optional[str]:
    match = type_pattern_1().search(page_text)
    if match:
        doc_type = match.group(1).lower()
        if doc_type in doc_type_mapping():
            return doc_type_mapping()[doc_type]
        return doc_type
    match = type_pattern_2().search(page_text)
    if match:
        return "nou"
    return None


def has_no_letters(text: str) -> bool:
    return bool(no_letters_pattern().match(text))


def clean_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def split_on_binding_word(text: str) -> list[str]:
    return binding_word_pattern().split(text)


def substitute_special_char_and_binding(text: str) -> str:
    return special_char_and_binding_pattern().sub('', text).replace("  ", " ").strip()


def substitute_non_alphanumeric(text: str) -> str:
    return non_alphanumeric_pattern().sub(' ', text).strip()


def has_non_author_keywords(text: str) -> bool:
    return bool(re.search(photograph_label(), text))
