"""This module deals with pages, defined as sets of text elements."""


from typing import Callable, Optional, Tuple, TypedDict
from fitz import Document
from . import text
from .text import ValueAndContext


class SpanType(TypedDict):
    """Spans are a structure returned by fitz/MuPDF"""
    text: str
    font: str
    size: float
    bbox: tuple[float, float, float, float]


class TextBlock:
    """A single text element, similar to spans.

    Attributes hold information on the text content, font, font size and position.
    The flags attribute is only used in the subclass InfoPage."""

    def __init__(self, span: SpanType):
        self.text = span['text'].replace('\xa0', ' ').strip()
        self.font = span['font']
        self.fontsize = span['size']
        self.bbox = span['bbox']
        self.flags = 0

    def __str__(self) -> str:
        return f"[{self.bbox[0]:.2f}, {self.bbox[1]:.2f}, " + \
            "{self.bbox[2]:.2f}, {self.bbox[3]:.2f}] " + \
            "{self.font} {self.fontsize:.2f} [{self.flags}]\t[{self.text}]"


class Page:
    """A Page object contains all text blocks on a given page of the document.

    The methods provided use position information to find values in neighouring
    blocks, for example an ISBN value that is next to (horizontally or vertically)
    a block stating "ISBN:".
    """

    # TODO: preserve full blocks instead of single lines?
    def __init__(self, doc: Document, page_number: int):
        self.text_blocks = []
        doc_page = doc.load_page(page_number - 1)
        blocks = doc_page.get_text("dict")['blocks']
        for block in blocks:
            if 'lines' in block.keys():
                for line in block['lines']:
                    spans = line['spans']
                    for span in spans:
                        if not span['text'].strip():
                            continue
                        self.text_blocks.append(TextBlock(span))

    def get_line_and_column(self, block: TextBlock,
                            slack_x: float = 5., slack_y: float = 5.,
                            require_letters: bool = False
                            ) -> Tuple[list[TextBlock], list[TextBlock]]:
        """Returns lists of blocks horizontally and vertically aligned with given block

        Given a block, this method returns 2 lists of blocks that are on the same line
        (resp. column), allowing for a slack_y (resp. slack_x) difference in coordinate.
        If require_letters is True, blocks with no letters are discarded.
        """

        def has_letters(string: str) -> bool:
            if require_letters:
                return not text.has_no_letters(string)
            return True

        blocks_on_line = [b for b in self.text_blocks
                          if abs(b.bbox[1] - block.bbox[1]) < slack_y
                          and b.bbox[0] > block.bbox[0]
                          and has_letters(b.text)]

        blocks_on_column = [b for b in self.text_blocks
                            if abs(b.bbox[0] - block.bbox[0]) < slack_x
                            and b.bbox[1] > block.bbox[1]
                            and has_letters(b.text)]

        return (blocks_on_line, blocks_on_column)

    def find_neighbour(self, block: TextBlock,
                       transform: Callable[[str], Optional[ValueAndContext]]
                       ) -> Optional[ValueAndContext]:
        """Returns text content of block's nearest neighbour on which `transform`
        method yields a truth value.
        """

        (blocks_on_line, blocks_on_column) = self.get_line_and_column(block)

        if blocks_on_line:
            block_text = transform(blocks_on_line[0].text)
            if block_text:
                return block_text

        if blocks_on_column:
            block_text = transform(blocks_on_column[0].text)
            if block_text:
                return block_text

        return None

    def find_isxn(self, identifier: str) -> list[ValueAndContext]:
        """Returns a list of all ISXN values found on page.

        The list contains ValueAndContext objects, so the surrouding context (text
        next to value or in label block) is returned as well.
        """
        values = []
        isxn_blocks = [b for b in self.text_blocks if identifier in b.text]
        for isxn_block in isxn_blocks:
            isxn = text.find_isxn(identifier, isxn_block.text)
            if not isxn:
                isxn = self.find_neighbour(
                    isxn_block,
                    lambda t: text.find_isxn(identifier, t)
                )
            if not isxn:
                continue
            isxn.append_to_context(isxn_block.text.lower())
            values.append(isxn)
        return values

    def find_publisher_block(self) -> Optional[TextBlock]:
        publisher_block = None
        for block in self.text_blocks:
            if text.publisher_label().match(block.text.lower()):
                publisher_block = block
                break
        return publisher_block

    def find_publisher(self) -> Optional[str]:
        publisher_block = self.find_publisher_block()
        if publisher_block:
            neighbour = self.find_neighbour(publisher_block, ValueAndContext)
            if neighbour:
                return neighbour.value
        return None
