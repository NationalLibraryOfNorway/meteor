"""Author name module, providing logic and methods to locate and parse authors' names"""


from typing import Optional
from metadata_extract import text
from .page import TextBlock
from .candidate import AuthorType


def concat_text_blocks_to_str(page: list[TextBlock]) -> str:
    """Concatenate text blocks to one string"""
    raw_text = ""
    for block in page:
        if is_probable_name_block(block.text) and remove_non_author_name(block.text):
            raw_text += ", " + block.text
    return raw_text


def get_author_names(text_block: str) -> Optional[list[str]]:
    """Perform all steps to extract author names from text and return list of authors"""
    author_text = remove_parenthesis(text_block)
    author_text_matched = match_text_name_regex(author_text)

    if not author_text_matched:
        return None

    authors = split_author_string(author_text_matched)
    authors = remove_multi_capital_letter(authors)
    authors = remove_duplicate_names(authors)
    return authors


def remove_multi_capital_letter(authors: list[str]) -> list[str]:
    """Remove all names with multiple sequential capital letters"""
    return [author for author in authors
            if not text.DOUBLE_CAPITAL_LETTER_PATTERN.search(author)]


def remove_non_author_name(name: str) -> Optional[str]:
    if text.has_non_author_keywords(name):
        return None
    return name


def remove_parenthesis(author_text: str) -> str:
    """Remove all parenthesis and text inside them"""
    parenthesis_match = text.PARENTHESIS_PATTERN.findall(author_text)
    if parenthesis_match:
        for match in parenthesis_match:
            author_text = author_text.replace(match, "")
    return author_text


def match_text_name_regex(author_text: str) -> Optional[str]:
    """Match all names in text to name_pattern regular expression"""
    name_match = text.NAME_PATTERN.findall(author_text)
    if name_match:
        author_text = ", ".join(name_match)
        return author_text
    return None


def split_author_string(author_text: str) -> list[str]:
    """Split author string into list of authors"""
    authors = text.split_on_binding_word(author_text)
    return [author.strip() for author in authors]


def remove_duplicate_names(authors: list[str]) -> list[str]:
    """If a name is present multiple times per page it will be added multiple times to the list
    This function removes all duplicate names"""
    authors = list(set(authors))
    return authors


def is_probable_name_block(text_block: str) -> bool:
    """Check if a text block is a probable name block by determining
    whether the entire line matches the name_pattern"""

    # Step 1: Remove parenthesis, "and"/"og" and other characters such as ;:,. and double whitespace
    text_block = remove_parenthesis(text_block)
    text_block = text.substitute_special_char_and_binding(text_block)

    # Step 2: Check if the block and the match have the same length
    match_block = "".join(text.NAME_PATTERN.findall(text_block))
    return len(text_block) == len(match_block)


def name_exists_in_title(title: str, name: str) -> bool:
    title_tokens = text.substitute_non_alphanumeric(title).lower()
    name_tokens = text.substitute_non_alphanumeric(name).lower()
    return name_tokens in title_tokens


def create_author_dict(name: str) -> AuthorType:
    first_name = " ".join(name.split()[:-1])
    last_name = name.split()[-1]
    return {"firstname": first_name, "lastname": last_name}


def is_all_caps_spaced(text_block: str) -> bool:
    """Words with all caps spaced letters will be captured as names
    This method prevents having to do this check in the regex"""
    for letter in text_block.split():
        if len(letter) != 1 or not letter.isupper():
            return False
    return True
