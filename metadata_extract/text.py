"""Text module, containing methods and logic dealing with strings and regexes."""

import re
from typing import Optional
import regex

from metadata_extract.init_files import InitFiles


class ValueAndContext:
    """Stores a text value with surrounding context"""
    def __init__(self, value: str, context: Optional[str] = None):
        self.value = value
        self.context = context

    def append_to_context(self, extra_context: str) -> None:
        self.context = (self.context or '') + extra_context


files = InitFiles()
LABELS = files.get_labels()
STOPWORDS = files.get_stopwords()

ISXN_PATTERN = {
    'ISSN': re.compile(r"\D(\d{4}[–-][\dX]{4})\D"),
    'ISBN': re.compile(r"\D([\d–-]{13,17})\D")
}
REPORT_PATTERN = re.compile(fr'^(\w+)\W({LABELS["report"]})\W', re.IGNORECASE)
TYPE_PATTERN_1 = re.compile(fr'\b({LABELS["reportType"]})\b', re.IGNORECASE)
TYPE_PATTERN_2 = re.compile(r'\bNOU\b')
DOC_TYPE_MAPPING = files.get_doc_type_mapping()
PUBLISHER_LABEL = re.compile(fr'({LABELS["publisher"]}):?', re.IGNORECASE)
NO_LETTERS_PATTERN = re.compile(r'^[\W\d]+$')
AUTHOR_LABEL = re.compile(fr'({LABELS["author"]}):?', re.IGNORECASE)
NAME_PATTERN = regex.compile(r"\b[^\P{Lu}][^\P{Ll}]*[-|‐]?[^\P{Lu}]?[^\P{Ll}’]*\.?" +
                             r"(?: [^\P{Lu}][^\P{Ll}’]*[-|‐]?[^\P{Lu}]?[^\P{Ll}]*\.?)+\b(?! *\()")
PARENTHESIS_PATTERN = re.compile(r"\(.*?\)")
DOUBLE_CAPITAL_LETTER_PATTERN = re.compile(r"\b[A-Z]{2,}\b")
BINDING_WORD_PATTERN = re.compile(fr'\b(?:{LABELS["bindingWords"]})\b|&|,')
SPECIAL_CHAR_AND_BINDING_PATTERN = re.compile(fr'[;:,.]|({LABELS["bindingWords"]})\b|&+')
NON_ALPHANUMERIC_PATTERN = re.compile(r"\W+")
PHOTOGRAPH_LABEL = re.compile(fr'\b({LABELS["photo"]})\b', re.IGNORECASE)


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
    match = REPORT_PATTERN.search(text + '.')
    if match:
        prefix = match.group(1)
        if prefix.isupper():
            return prefix
    return None


def find_doc_type(page_text: str) -> Optional[str]:
    match = TYPE_PATTERN_1.search(page_text)
    if match:
        doc_type = match.group(1).lower()
        if doc_type in DOC_TYPE_MAPPING:
            return DOC_TYPE_MAPPING[doc_type]
        return doc_type
    match = TYPE_PATTERN_2.search(page_text)
    if match:
        return "nou"
    return None


def has_no_letters(text: str) -> bool:
    return bool(NO_LETTERS_PATTERN.match(text))


def clean_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def split_on_binding_word(text: str) -> list[str]:
    return BINDING_WORD_PATTERN.split(text)


def substitute_special_char_and_binding(text: str) -> str:
    return SPECIAL_CHAR_AND_BINDING_PATTERN.sub('', text).replace("  ", " ").strip()


def substitute_non_alphanumeric(text: str) -> str:
    return NON_ALPHANUMERIC_PATTERN.sub(' ', text).strip()


def has_non_author_keywords(text: str) -> bool:
    return bool(re.search(PHOTOGRAPH_LABEL, text))
