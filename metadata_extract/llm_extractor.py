"""The LLM extractor module extracts metadata using an external LLM API service."""

from typing import TypedDict
import json
import requests
from .candidate import AuthorType, Candidate, Origin
from .metadata import Metadata
from .meteor_document import MeteorDocument


class LLMConfig(TypedDict):
    """Configuration for LLM API service"""
    api_url: str
    api_key: str
    model: str


class LLMExtractor:
    """A LLMExtractor object loads a MeteorDocument and fills a Metadata object
    by performing a call to an external LLM API service."""

    SYSTEM_PROMPT = "You are a skilled librarian specialized in meticulous " + \
                    "cataloguing of digital documents."
    INSTRUCTION = "Extract metadata from this document. Return as JSON."
    MAX_TOKENS = 1024
    TEMPERATURE = 0.0
    TIMEOUT = 120

    def __init__(self, doc: MeteorDocument, llm_config: LLMConfig):
        self._doc = doc
        self._config = llm_config
        self.metadata = Metadata()

    def extract_metadata(self) -> None:
        doc_json = self._doc.extract_text_as_json()
        response = self._llm_request(doc_json)
        self._parse_response_to_doc(response)

    def _llm_request(self, doc_json: str) -> str:
        message = f"{self.INSTRUCTION}\n\n{doc_json}"

        if self._config['api_url'].endswith("/"):
            url = self._config['api_url'] + "chat/completions"
        else:
            url = self._config['api_url'] + "/chat/completions"

        headers = {
            "Content-Type": "application/json"
        }

        if self._config['api_key']:
            headers['Authorization'] = f'Bearer {self._config["api_key"]}'

        data = {
            "model": self._config['model'],
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            "temperature": self.TEMPERATURE,
            "max_tokens": self.MAX_TOKENS
        }

        api_response = requests.post(url,
                                     headers=headers,
                                     json=data,
                                     timeout=self.TIMEOUT)

        api_response.raise_for_status()
        return str(api_response.json()['choices'][0]['message']['content'])

    def _parse_response_to_doc(self, response: str) -> None:
        metadata = json.loads(response)

        # language
        if 'language' in metadata:
            self.metadata.add_candidate('language', Candidate(metadata['language'], Origin.LLM))

        # title
        if 'title' in metadata:
            self.metadata.add_candidate('title', Candidate(metadata['title'], Origin.LLM))

        # creator
        if 'creator' in metadata:
            for creator in metadata['creator']:
                lastname, firstname = creator.split(', ', maxsplit=1)
                author_dict: AuthorType = {"firstname": firstname, "lastname": lastname}
                self.metadata.add_candidate('author', Candidate(author_dict, Origin.LLM))

        # year
        if 'year' in metadata:
            self.metadata.add_candidate('year', Candidate(metadata['year'], Origin.LLM))

        # publisher
        if 'publisher' in metadata:
            for publisher in metadata['publisher']:
                # FIXME should we look up publisher in registry like Finder does?
                self.metadata.add_candidate('publisher', Candidate(publisher, Origin.LLM))

        # doi - not supported by Meteor

        # e-isbn
        if 'e-isbn' in metadata:
            # This is pretty poor, we just pass the found e-ISBNs (almost never more than one)
            # to Meteor directly and let it pick one essentially at random
            for e_isbn in metadata['e-isbn']:
                self.metadata.add_candidate('ISBN', Candidate(e_isbn, Origin.LLM))

        # p-isbn - Meteor isn't interested in printed ISBNs

        # e-issn
        if 'e-issn' in metadata:
            self.metadata.add_candidate('ISSN', Candidate(metadata['e-issn'], Origin.LLM))

        # p-issn - Meteor isn't interested in printed ISBNs

        # type_coar - not supported by Meteor