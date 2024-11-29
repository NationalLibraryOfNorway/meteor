"""Metadata module

Handling and selecting the candidate values found in the document
"""


from typing import Optional, TypedDict
from . import text
from .candidate import Candidate, CandidateType, Origin


class Results(TypedDict):
    """Type of Meteor output"""
    year: Optional[CandidateType]
    language: Optional[CandidateType]
    title: Optional[CandidateType]
    publisher: Optional[CandidateType]
    publicationType: Optional[CandidateType]
    authors: list[CandidateType]
    isbn: Optional[CandidateType]
    issn: Optional[CandidateType]


def new_results() -> Results:
    return {
        'year': None,
        'language': None,
        'title': None,
        'publisher': None,
        'publicationType': None,
        'authors': [],
        'isbn': None,
        'issn': None
    }


class Metadata:
    """A Metadata object has two purposes: first, store all candidate values found in
    the meteor document ; second, implement the logic deciding which ones will be
    returned in the final Results object.
    """

    def __init__(self) -> None:
        self.candidates: dict[str, list[Candidate]] = {}
        self.results: Results = new_results()

    def add_candidate(self, field: str, candidate: Candidate) -> None:
        if field not in self.candidates:
            self.candidates[field] = []
        self.candidates[field].append(candidate)

    def has_publisher(self, name: str) -> bool:
        if 'publisher' not in self.candidates:
            return False
        return name in [c.value for c in self.candidates['publisher']]

    def has_publisher_from_infopage(self) -> bool:
        if 'publisher' not in self.candidates:
            return False
        for candidate in self.candidates['publisher']:
            if candidate.origin == Origin.INFO_PAGE:
                return True
        return False

    @staticmethod
    def year_ranking(candidate: Candidate) -> int:
        if candidate.origin == Origin.COPYRIGHT:
            return 2
        if candidate.origin == Origin.PDFINFO:
            return 1
        return 0

    def rank_years(self) -> Optional[CandidateType]:
        if 'year' not in self.candidates:
            return None
        sorted_years = sorted(self.candidates['year'],
                              key=Metadata.year_ranking,
                              reverse=True)
        return sorted_years[0].to_dict()

    def choose_language(self) -> Optional[CandidateType]:
        if 'language' not in self.candidates:
            return None
        return self.candidates['language'][0].to_dict()

    def choose_isxn(self, identifier: str) -> Optional[CandidateType]:
        if identifier not in self.candidates:
            return None
        isxn_values = {}
        for isxn in self.candidates[identifier]:
            if isxn.value not in isxn_values:
                isxn_values[isxn.value] = text.score_isxn_context(isxn.context)

        sorted_dict = sorted(isxn_values.items(), key=lambda x: -x[1])
        for k in sorted_dict:
            for candidate in self.candidates[identifier]:
                if candidate.value == k[0]:
                    return candidate.to_dict()
        return None

    def choose_title(self) -> Optional[CandidateType]:
        # TODO: avoid type check in list comprehensions below
        if 'title' not in self.candidates:
            return None
        pdfinfo_title = [c for c in self.candidates['title'] if
                         c.origin == Origin.PDFINFO and isinstance(c.value, str)
                         and not text.has_no_letters(c.value)]
        if pdfinfo_title:
            return pdfinfo_title[0].to_dict()
        page_title = [c for c in self.candidates['title'] if
                      c.origin == Origin.FRONT_PAGE and isinstance(c.value, str)
                      and not text.has_no_letters(c.value)]
        if page_title:
            return page_title[0].to_dict()
        llm_title = [c for c in self.candidates['title'] if
                     c.origin == Origin.LLM and isinstance(c.value, str)
                     and not text.has_no_letters(c.value)]
        if llm_title:
            return llm_title[0].to_dict()
        return None

    def choose_publishers(self) -> Optional[CandidateType]:
        if 'publisher' not in self.candidates:
            return None
        publishers = self.candidates['publisher']
        publishers_in_registry = [p for p in publishers if p.reg_entries]
        if publishers_in_registry:
            return publishers_in_registry[0].to_dict()
        return publishers[0].to_dict()

    def choose_doc_type(self) -> Optional[CandidateType]:
        if 'document_type' not in self.candidates:
            return None
        return self.candidates['document_type'][0].to_dict()

    def choose_authors(self) -> list[CandidateType]:
        if 'author' not in self.candidates:
            return []
        authors: list[CandidateType] = []
        for candidate in self.candidates['author']:
            entry = candidate.to_dict()
            if any((a['firstname'], a['lastname']) == (entry['firstname'], entry['lastname'])
                    for a in authors):
                continue
            authors.append(entry)
        return authors

    def choose_best(self) -> None:
        self.results['year'] = self.rank_years()
        self.results['language'] = self.choose_language()
        self.results['title'] = self.choose_title()
        self.results['publisher'] = self.choose_publishers()
        self.results['publicationType'] = self.choose_doc_type()
        self.results['authors'] = self.choose_authors()
        self.results['isbn'] = self.choose_isxn('ISBN')
        self.results['issn'] = self.choose_isxn('ISSN')
