"""Module for storing definitions of shared dataclasses / TypedDict"""


from typing import TypedDict


class SpanType(TypedDict):
    """Spans are a structure returned by fitz/MuPDF"""
    text: str
    font: str
    size: float
    bbox: tuple[float, float, float, float]
