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


def __labels() -> dict[str, str]:
    return ResourceLoader.get_labels()


__PATTERNS: dict[str, Pattern[str]] = {
    'ISSN': re.compile(r"\D(\d{4}[–-][\dX]{4})\D"),
    'ISBN': re.compile(r"\D([\d–-]{13,17})\D")
}
__NAME_PATTERN: dict[str, regex.regex.Pattern[str]] = {}


def issn_pattern() -> Pattern[str]:
    if 'ISSN' not in __PATTERNS:
        __PATTERNS['ISSN'] = re.compile(r"\D(\d{4}[–-][\dX]{4})\D")
    return __PATTERNS['ISSN']


def isbn_pattern() -> Pattern[str]:
    if 'ISBN' not in __PATTERNS:
        __PATTERNS['ISBN'] = re.compile(r"\D([\d–-]{13,17})\D")
    return __PATTERNS['ISBN']


def report_pattern() -> Pattern[str]:
    if 'report' not in __PATTERNS:
        __PATTERNS['report'] = re.compile(fr'^(\w+)\W({__labels()["report"]})\W', re.IGNORECASE)
    return __PATTERNS['report']


def type_pattern_1() -> Pattern[str]:
    if 'type_pattern_1' not in __PATTERNS:
        __PATTERNS['type_pattern_1'] = re.compile(
            fr'\b({__labels()["reportType"]})\b', re.IGNORECASE
        )
    return __PATTERNS['type_pattern_1']


def type_pattern_2() -> Pattern[str]:
    if 'type_pattern_2' not in __PATTERNS:
        __PATTERNS['type_pattern_2'] = re.compile(r'\bNOU\b')
    return __PATTERNS['type_pattern_2']


def publisher_label() -> Pattern[str]:
    if 'publisher' not in __PATTERNS:
        __PATTERNS['publisher'] = re.compile(fr'({__labels()["publisher"]}):?', re.IGNORECASE)
    return __PATTERNS['publisher']


def no_letters_pattern() -> Pattern[str]:
    if 'no_letters' not in __PATTERNS:
        __PATTERNS['no_letters'] = re.compile(r'^[\W\d]+$')
    return __PATTERNS['no_letters']


def author_label() -> Pattern[str]:
    if 'author' not in __PATTERNS:
        __PATTERNS['author'] = re.compile(fr'({__labels()["author"]}):?', re.IGNORECASE)
    return __PATTERNS['author']


def name_pattern() -> regex.regex.Pattern[str]:
    if 'name' not in __NAME_PATTERN:
        __NAME_PATTERN['name'] = regex.compile(
            r"\b[^\P{Lu}][^\P{Ll}]*[-|‐]?[^\P{Lu}]?[^\P{Ll}’]*\.?" +
            r"(?: [^\P{Lu}][^\P{Ll}’]*[-|‐]?[^\P{Lu}]?[^\P{Ll}]*\.?)+\b(?! *\()")
    return __NAME_PATTERN['name']


def parenthesis_pattern() -> Pattern[str]:
    if 'parenthesis' not in __PATTERNS:
        __PATTERNS['parenthesis'] = re.compile(r"\(.*?\)")
    return __PATTERNS['parenthesis']


def double_capital_letter_pattern() -> Pattern[str]:
    if 'double_capital_letter' not in __PATTERNS:
        __PATTERNS['double_capital_letter'] = re.compile(r"\b[A-Z]{2,}\b")
    return __PATTERNS['double_capital_letter']


def binding_word_pattern() -> Pattern[str]:
    if 'binding_word' not in __PATTERNS:
        __PATTERNS['binding_word'] = re.compile(fr'\b(?:{__labels()["bindingWords"]})\b|&|,')
    return __PATTERNS['binding_word']


def special_char_and_binding_pattern() -> Pattern[str]:
    if 'special_char_and_binding' not in __PATTERNS:
        __PATTERNS['special_char_and_binding'] = re.compile(
            fr'[;:,.]|({__labels()["bindingWords"]})\b|&+'
        )
    return __PATTERNS['special_char_and_binding']


def non_alphanumeric_pattern() -> Pattern[str]:
    if 'non_alphanumeric' not in __PATTERNS:
        __PATTERNS['non_alphanumeric'] = re.compile(r"\W+")
    return __PATTERNS['non_alphanumeric']


def photograph_label() -> Pattern[str]:
    if 'photograph' not in __PATTERNS:
        __PATTERNS['photograph'] = re.compile(fr'\b({__labels()["photo"]})\b', re.IGNORECASE)
    return __PATTERNS['photograph']


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
    match = __PATTERNS[identifier].search("." + text + ".")
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
        if doc_type in ResourceLoader.get_doc_type_mapping():
            return ResourceLoader.get_doc_type_mapping()[doc_type]
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
