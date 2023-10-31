import xml.etree.ElementTree as ET
from functools import reduce
from pathlib import Path
from typing import TypedDict
from .models import SpanType


class BlockType(TypedDict):
    # TODO: add font and fontsize
    text: str
    bbox: list[float]


class AltoFile:

    MAX_SPACING = 80  # Arbitrary value...
    SPACES = ['TopMargin', 'LeftMargin', 'RightMargin', 'BottomMargin', 'PrintSpace']

    def __init__(self, path: Path) -> None:
        tree = ET.parse(path)
        self.root = tree.getroot()
        self.styles = self.get_styles()
        self.blocks = self.get_all_blocks()
        self.spans, self.full_text = self.parse_blocks()

    def get_styles(self) -> dict[str, dict[str, str]]:
        # styles are specified for TextBlock/String (not TextLine?)
        doc_styles: dict[str, dict[str, str]] = {}
        styles_element = self.root.find('Styles')
        if not styles_element:
            return doc_styles
        # TODO: group styles?
        for style_et in styles_element.findall('TextStyle'):
            att = style_et.attrib
            doc_styles[att['ID']] = {
                'font': att['FONTFAMILY'],
                'fontsize': att['FONTSIZE']
            }
        return doc_styles

    def get_all_blocks(self) -> list[ET.Element]:
        all_blocks: list[ET.Element] = []
        # content = self.root.find('Layout').find('Page')
        layout = self.root.find('Layout')
        if not layout:
            return all_blocks
        page = layout.find('Page')
        if not page:
            return all_blocks
        for space in AltoFile.SPACES:
            space_content = page.find(space)
            if not space_content:
                continue
            blocks = space_content.findall('TextBlock')
            all_blocks.extend(blocks)

            composed = space_content.findall('ComposedBlock')
            for comp in composed:
                blocks = comp.findall('TextBlock')
                all_blocks.extend(blocks)
        return all_blocks

    def parse_blocks(self) -> tuple[list[SpanType], str]:
        lines_str = []
        spans: list[SpanType] = []
        for block in self.blocks:
            lines = block.findall('TextLine')
            for line in lines:
                elements, fulltext = AltoFile.parse_line(line)
                for el in elements:
                    spans.append({
                        'text': el['text'],
                        'font': 'DEFAULT_FONT',
                        'size': 10,
                        'bbox': (el['bbox'][0], el['bbox'][1], el['bbox'][2], el['bbox'][3])
                    })
                lines_str.append(fulltext)
        return spans, '\n'.join(lines_str)

    @staticmethod
    def get_position(element: ET.Element) -> list[float]:

        """Converts positions written as string-values HPOS/VPOS/WIDTH/HEIGHT to
        float-valued bounding-box [x0,y0,x1,y1]"""

        for att in ['HPOS', 'VPOS', 'WIDTH', 'HEIGHT']:
            if att not in element.attrib:
                raise ValueError(f'Attribute {att} missing, cannot make bbox')

        return [
            float(element.attrib['HPOS']),
            float(element.attrib['VPOS']),
            float(element.attrib['HPOS']) + float(element.attrib['WIDTH']),
            float(element.attrib['VPOS']) + float(element.attrib['HEIGHT'])
        ]

    @staticmethod
    def merge(acc: list[BlockType], word: BlockType) -> list[BlockType]:

        """Accumulator function: `word` block will be merged in the last item
        in `acc` list if the horizontal gap is smaller than MAX_SPACING"""

        if not acc:
            return [word]

        current_block = acc[-1]
        if word['bbox'][0] - current_block['bbox'][2] < AltoFile.MAX_SPACING:
            current_block['bbox'][1] = min(word['bbox'][1], current_block['bbox'][1])
            current_block['bbox'][2] = word['bbox'][2]
            current_block['bbox'][3] = max(word['bbox'][3], current_block['bbox'][3])
            current_block['text'] += ' ' + word['text']
        else:
            acc.extend([word])
        return acc

    @staticmethod
    def parse_line(line_element: ET.Element) -> tuple[list[BlockType], str]:
        word_elements: list[BlockType] = []
        words = line_element.findall('String')
        for word in words:
            word_elements.append({
                'text': word.attrib['CONTENT'],
                'bbox': AltoFile.get_position(word)
            })
        grouped_blocks: list[BlockType] = reduce(AltoFile.merge, word_elements, [])
        single_string = ' '.join([block['text'] for block in grouped_blocks])
        return grouped_blocks, single_string
