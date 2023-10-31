from typing import TypedDict


class SpanType(TypedDict):
    """Spans are a structure returned by fitz/MuPDF"""
    text: str
    font: str
    size: float
    bbox: tuple[float, float, float, float]
