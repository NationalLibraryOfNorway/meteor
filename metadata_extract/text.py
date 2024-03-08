"""Text module, containing methods and logic dealing with strings and regexes."""

from typing import Optional

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


__PATTERNS: dict[str, regex.regex.Pattern[str]] = {
    'ISSN': regex.compile(r"\D(\d{4}[–-][\dX]{4})\D"),
    'ISBN': regex.compile(r"\D([\d–-]{13,17})\D"),
    'type_pattern_2': regex.compile(r'\bNOU\b'),
    'no_letters_pattern': regex.compile(r'^[\W\d]+$'),
    'name_pattern': regex.compile(
        r"\b[^\P{Lu}][‘’‛′']?[^\P{Ll}]*[-|‐]?[^\P{Lu}]?[‘’‛′']?[^\P{Ll}]*\.?" +
        r"(?: [^\P{Lu}][‘’‛′']?[^\P{Ll}]*[-|‐]?[^\P{Lu}]?[‘’‛′']?[^\P{Ll}]*\.?)+\b(?! *\()"),
    'parenthesis_pattern': regex.compile(r"\(.*?\)"),
    'double_capital_letter_pattern': regex.compile(r"\b[A-Z]{2,}\b"),
    'non_alphanumeric_pattern': regex.compile(r"\W+")
}


def report_pattern() -> regex.regex.Pattern[str]:
    if 'report' not in __PATTERNS:
        __PATTERNS['report'] = regex.compile(fr'^(\w+)\W({__labels()["report"]})\W(?i)')
    return __PATTERNS['report']


def type_pattern_1() -> regex.regex.Pattern[str]:
    if 'type_pattern_1' not in __PATTERNS:
        __PATTERNS['type_pattern_1'] = regex.compile(
            fr'\b({__labels()["reportType"]})\b(?i)'
        )
    return __PATTERNS['type_pattern_1']


def type_pattern_2() -> regex.regex.Pattern[str]:
    return __PATTERNS['type_pattern_2']


def publisher_label() -> regex.regex.Pattern[str]:
    if 'publisher' not in __PATTERNS:
        __PATTERNS['publisher'] = regex.compile(fr'({__labels()["publisher"]}):?(?i)')
    return __PATTERNS['publisher']


def no_letters_pattern() -> regex.regex.Pattern[str]:
    return __PATTERNS['no_letters_pattern']


def author_label() -> regex.regex.Pattern[str]:
    if 'author' not in __PATTERNS:
        __PATTERNS['author'] = regex.compile(fr'({__labels()["author"]}):?(?i)')
    return __PATTERNS['author']


def name_pattern() -> regex.regex.Pattern[str]:
    return __PATTERNS['name_pattern']


def parenthesis_pattern() -> regex.regex.Pattern[str]:
    return __PATTERNS['parenthesis_pattern']


def double_capital_letter_pattern() -> regex.regex.Pattern[str]:
    return __PATTERNS['double_capital_letter_pattern']


def binding_word_pattern() -> regex.regex.Pattern[str]:
    if 'binding_word' not in __PATTERNS:
        __PATTERNS['binding_word'] = regex.compile(fr'\b(?:{__labels()["bindingWords"]})\b|&|,')
    return __PATTERNS['binding_word']


def special_char_and_binding_pattern() -> regex.regex.Pattern[str]:
    if 'special_char_and_binding' not in __PATTERNS:
        __PATTERNS['special_char_and_binding'] = regex.compile(
            fr'[;:,.]|({__labels()["bindingWords"]})\b|&+'
        )
    return __PATTERNS['special_char_and_binding']


def non_alphanumeric_pattern() -> regex.regex.Pattern[str]:
    return __PATTERNS['non_alphanumeric_pattern']


def photograph_label() -> regex.regex.Pattern[str]:
    if 'photograph' not in __PATTERNS:
        __PATTERNS['photograph'] = regex.compile(fr'\b({__labels()["photo"]})\b(?i)')
    return __PATTERNS['photograph']


def find_in_pages(title: str, pages: dict[int, str], max_pages: int = 3) -> int:
    """Tries to find the <title> argument in the pages dictionary.

    Optional argument to stop the search after <max_pages> pages.
    Returns page number (starts at 1) if the title is found or 0 otherwise."""
    title_tokens = regex.sub(r'\W+', ' ', title).strip()
    for page_number in range(min(len(pages), max_pages)):
        page_tokens = regex.sub(r'\W+', ' ', pages[page_number + 1]).strip()
        if f' {title_tokens} ' in f' {page_tokens} ':
            return page_number + 1
    return 0


def find_isxn(identifier: str, text: str) -> Optional[ValueAndContext]:
    match = __PATTERNS[identifier].search("." + text + ".")
    if match:
        return ValueAndContext(regex.sub('–', '-', match.group(1)), text.lower())
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
    return regex.sub(r'\s+', ' ', text).strip()


def split_on_binding_word(text: str) -> list[str]:
    return binding_word_pattern().split(text)


def substitute_special_char_and_binding(text: str) -> str:
    return special_char_and_binding_pattern().sub('', text).replace("  ", " ").strip()


def substitute_non_alphanumeric(text: str) -> str:
    return non_alphanumeric_pattern().sub(' ', text).strip()


def has_non_author_keywords(text: str) -> bool:
    return bool(regex.search(photograph_label(), text))


def score_isxn_context(context: Optional[str]) -> int:
    if not context:
        return 0
    score = 0
    e_matches = regex.findall(fr'{__labels()["e_isxn"]}|\be\b', context)
    score += len(e_matches)
    p_matches = regex.findall(fr'{__labels()["p_isxn"]}|\bp\b', context)
    score -= len(p_matches)
    return score
