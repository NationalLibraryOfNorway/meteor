"""InfoPage module deals with pages containing information structured as a list or table"""


from typing import Optional, TypedDict
from fitz import Document

from . import text
from .author_name import get_author_names
from .resource_loader import ResourceLoader
from .page import Page, TextBlock


class BlockAndScore(TypedDict):
    """Holds a penalty score for a TextBlock. Used in InfoPage.get_value_neighbour"""
    block: TextBlock
    score: int


class InfoPage(Page):
    """Extends a Page by attempting to classify text blocks as labels or values.

    Information pages in reports often contain a page formatted as a list or a table
    with labels and values. By using a keyword list, an InfoPage object first tries
    to find if a specific format is used for label-blocks. It then uses these flags
    to return the text content of the neighbour least likely to be a label-block.
    """

    UPPERCASE = 1
    ENDSWITHCOLON = 2
    HASKEYWORD = 4
    KEYWORDFONT = 8

    @staticmethod
    def find_page_number(pages: dict[int, str]) -> int:
        """Looks for the info page, based on a keyword list.

        Returns either the page number (starts at 1) or 0 if no such page is found.
        """
        scores: dict[int, int] = {}
        for page in pages:
            score = 0
            for k in ResourceLoader.get_info_page_keywords():
                if k in pages[page].lower():
                    score += 1
            scores[page] = score
        if max(scores.values()) == 0:
            return 0
        sorted_pages = sorted(scores.items(), key=lambda x: -x[1])
        return sorted_pages[0][0]

    @staticmethod
    def keyword_appears_in(string: str) -> bool:
        for k in ResourceLoader.get_info_page_keywords():
            if k in string.lower():
                return True
        return False

    def __init__(self, doc: Document, pagenr: int):
        super().__init__(doc, pagenr)

        self.keyword_font = self.group_by_font()
        self.upper_attr = False
        self.colon_attr = False

        for block in self.text_blocks:
            if block.text.isupper():
                block.flags |= InfoPage.UPPERCASE
            if block.text.rstrip().endswith(':'):
                block.flags |= InfoPage.ENDSWITHCOLON
            if InfoPage.keyword_appears_in(block.text):
                block.flags |= InfoPage.HASKEYWORD
            if self.keyword_font and block.font == self.keyword_font:
                block.flags |= InfoPage.KEYWORDFONT

        self.check_attributes()

    def get_value_neighbour(self, block: TextBlock,
                            slack_x: float = 10., slack_y: float = 10.) -> Optional[str]:
        """Returns the text content of the neighbour block that is least likely to be a label."""

        candidates: list[BlockAndScore] = []

        (blocks_on_line, blocks_on_column) = super().get_line_and_column(block, slack_x=slack_x,
                                                                         slack_y=slack_y,
                                                                         require_letters=True)
        if blocks_on_line:
            candidates.append({'block': min(blocks_on_line, key=lambda b: b.bbox[0]),
                               'score': 0})
        if blocks_on_column:
            candidates.append({'block': min(blocks_on_column, key=lambda b: b.bbox[1]),
                               'score': 0})

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]['block'].text

        # For each candidate, compute a penalty score depending on attributes found for this
        # infopage's label blocks in the group_by_font and check_attributes methods.
        for candidate in candidates:
            candidate_block = candidate['block']
            if candidate_block.flags & InfoPage.KEYWORDFONT:
                candidate['score'] += 1
            if candidate_block.flags & InfoPage.UPPERCASE and self.upper_attr:
                candidate['score'] += 1
            if candidate_block.flags & InfoPage.ENDSWITHCOLON and self.colon_attr:
                candidate['score'] += 1

        # Sort and return content of block having the lowest penalty, i.e being least likely
        # of being a label.
        candidates.sort(key=lambda c: c['score'])
        return candidates[0]['block'].text

    def find_title(self) -> Optional[str]:
        title_block = None
        for block in self.text_blocks:
            if 'title' in block.text.lower() or 'tittel' in block.text.lower():
                title_block = block
                break
        if title_block:
            title = self.get_value_neighbour(title_block)
            return title
        return None

    def find_publisher(self) -> Optional[str]:
        publisher_block = super().find_publisher_block()
        if publisher_block:
            publisher = self.get_value_neighbour(publisher_block)
            return publisher
        return None

    def find_author(self) -> Optional[list[str]]:
        author_block = None
        for block in self.text_blocks:
            if text.author_label().match(block.text.lower()):
                author_block = block
                break
        if author_block:
            author_text = self.get_value_neighbour(author_block)
            if author_text:
                return get_author_names(author_text)
        return None

    def group_by_font(self) -> Optional[str]:
        """Heuristic checking if a specific font is used for label blocks."""
        fonts = {b.font for b in self.text_blocks}
        block_by_font = {}
        for font in fonts:
            block_by_font[font] = [b for b in self.text_blocks if b.font == font]
        proportions = {}
        for font, blocks in block_by_font.items():
            subset = [b for b in blocks if b.flags & InfoPage.HASKEYWORD]
            proportions[font] = len(subset) / float(len(blocks))
        if max(proportions.values()) < 0.5:
            return None
        sorted_fonts = sorted(proportions.items(), key=lambda x: -x[1])
        return sorted_fonts[0][0]

    def check_attributes(self) -> None:
        """Heuristics to determine if label blocks are formatted in a particular way.

        Based on a keyword list and formal attributes commonly used for labels (uppercase,
        ends with colon), this method computes ratios to check whether such formatting is used.
        """
        colon_block = [b for b in self.text_blocks if b.flags & InfoPage.ENDSWITHCOLON]
        if colon_block:
            colon_keywords = [b for b in colon_block if b.flags & InfoPage.HASKEYWORD]
            ratio_keywords_colon = len(colon_keywords) / float(len(colon_block))
            self.colon_attr = len(colon_block) > 0 and ratio_keywords_colon > 0.5

        upper_block = [b for b in self.text_blocks if b.flags & InfoPage.UPPERCASE and
                       not ('ISBN' in b.text or 'ISSN' in b.text)]
        if upper_block:
            upper_keywords = [b for b in upper_block if b.flags & InfoPage.HASKEYWORD]
            ratio_keywords_upper = len(upper_keywords) / float(len(upper_block))
            self.upper_attr = len(upper_block) > 0 and ratio_keywords_upper > 0.5
