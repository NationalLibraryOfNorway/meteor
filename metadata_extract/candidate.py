"""The module contains the class definitions for individual metadata candidates"""


from enum import Enum
from typing import Optional, TypedDict, Union, NotRequired
from .registry import RegistryType


class Origin(Enum):
    """Enumeration of possible origins for candidates"""
    FRONT_PAGE = 1
    PAGE = 2
    INFO_PAGE = 3
    PDFINFO = 4
    COPYRIGHT = 5
    RAPPORT_PREFIX = 6
    LANGUAGE_MODEL = 7
    LLM = 8


class OriginType(TypedDict):
    """Full origin type, with optional page number to specify provenance further"""
    type: str
    pageNumber: NotRequired[int]


class AuthorType(TypedDict):
    """Simple class representing a person's name"""
    firstname: str
    lastname: str


ValueType = Union[int, str, AuthorType]


class CandidateType(TypedDict):
    """JSON-serializable type for candidates.

    Origin is always set.
    Either firstname/lastname (for authors) or value (for all other field) are always set.
    authId and valueInDoc are specific to publisher field.
    """
    origin: OriginType
    value: NotRequired[Union[str, int]]
    firstname: NotRequired[str]
    lastname: NotRequired[str]
    authId: NotRequired[int]
    valueInDoc: NotRequired[str]


class Candidate:
    """Type for metadata candidates used in finder module"""
    def __init__(self, value: ValueType, origin: Origin,
                 page_nr: Optional[int] = None,
                 context: Optional[str] = None):
        self.value = value
        self.origin = origin
        self.page_nr = page_nr
        self.context = context
        self.reg_entries: list[RegistryType] = []

    def to_dict(self) -> CandidateType:
        origin_dict: OriginType = {'type': self.origin.name}
        if self.page_nr:
            origin_dict.update({'pageNumber': self.page_nr})

        candidate_dict: CandidateType = {'origin': origin_dict}

        # TODO: restructure class to avoid type check
        if isinstance(self.value, (int, str)):
            if self.reg_entries:
                candidate_dict.update({'value': self.reg_entries[0]['name'],
                                       'authId': self.reg_entries[0]['authId'],
                                       'valueInDoc': str(self.value)})
            else:
                candidate_dict.update({'value': self.value})
        else:
            candidate_dict.update({'firstname': self.value['firstname'],
                                   'lastname': self.value['lastname']})

        return candidate_dict
