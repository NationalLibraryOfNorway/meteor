"""Diff-script: write new Meteor results for evaluation files and checks differences

This script has to be executed with the new version of Meteor. After the new Meteor
results are written, a diff is run on the chosen field.
"""


# pylint: disable=broad-exception-caught, wrong-import-position, wrong-import-order

import argparse
import json
import os
import sys
from enum import Enum
from typing import TypedDict

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from metadata_extract.candidate import CandidateType  # noqa: E402
from metadata_extract.metadata import Results  # noqa: E402
from metadata_extract.meteor import Meteor  # noqa: E402

from decouple import config  # noqa: E402
from deepdiff import DeepDiff  # noqa: E402


class MetadataField(Enum):
    """List of fields in Meteor results"""
    TITLE: str = 'title'
    PUBLISHER: str = 'publisher'
    YEAR: str = 'year'
    ISBN: str = 'isbn'
    ISSN: str = 'issn'
    AUTHORS: str = 'authors'
    LANGUAGE: str = 'language'
    PUBLICATION_TYPE: str = 'publicationType'


class ResultData(TypedDict):
    """Metadata values for a given evaluation document"""
    doc_id: int
    metadata: Results | CandidateType | list[CandidateType]


response_data: list[ResultData] = []
fields = [field.value for field in MetadataField]
meteor = Meteor()


with open('diff/previous_results.json', 'r', encoding="UTF-8") as old_res_file:
    old_data = json.load(old_res_file)


def fetch_files() -> None:
    pdf_folder_path = config('EVAL_FILES_FOLDER')
    pdf_files = os.listdir(pdf_folder_path)

    for file in pdf_files:
        print(f"Processing file {file}")
        try:
            response = meteor.run(pdf_folder_path + "/" + file)
        except Exception as ex:
            # Some files might be corrupted and not return a response
            # We skip these files and continue. They are not included in the results
            print(f"Error while processing file {file}: {ex}")
            continue
        append_result(response, int(file.split(".")[0]))

    with open('diff/current_results.json', 'w', encoding="UTF-8") as new_res_file:
        json.dump(response_data, new_res_file, ensure_ascii=False, indent=2)


def append_result(response: Results, doc_id: int) -> None:
    result: ResultData = {
        'doc_id': doc_id,
        'metadata': response
    }
    response_data.append(result)


def transform_object_metadata(data: list[ResultData], metadata_field: str) -> None:
    for obj in data:
        try:
            metadata_obj = obj['metadata'][metadata_field]  # type: ignore
            obj['metadata'] = {metadata_field: metadata_obj}  # type: ignore
        except KeyError:
            continue


def repr_nullable(metadata_field: dict[str, str]) -> str | int:
    return metadata_field['value'] if metadata_field else '[VALUE NOT PRESENT]'


def compare_versions(metadata_field: str) -> None:
    if metadata_field is None or metadata_field == "" or metadata_field not in fields:
        metadata_field = 'title'

    print(f"\nComparing metadata field {metadata_field}")
    with open('diff/current_results.json', 'r', encoding="UTF-8") as new_res_file:
        new_data = json.load(new_res_file)

    transform_object_metadata(new_data, metadata_field)
    transform_object_metadata(old_data, metadata_field)

    for old_obj in old_data:
        for new_obj in new_data:
            if old_obj['doc_id'] == new_obj['doc_id']:
                try:
                    print_diff(old_obj, new_obj, metadata_field)
                except KeyError:
                    continue


def print_diff(old_obj: ResultData, new_obj: ResultData, metadata_field: str) -> None:
    old = old_obj['metadata'][metadata_field]  # type: ignore
    new = new_obj['metadata'][metadata_field]  # type: ignore
    diff = DeepDiff(old, new, ignore_order=True)
    if diff:
        print(f'\033[97m \nDoc_id: {old_obj["doc_id"]}')
        if metadata_field == 'authors':
            print('\033[31m [OLD] ' + str(old))
            print('\033[32m [NEW] ' + str(new))
            print(f"\033[97m {diff}")
        else:
            print('\033[31m [OLD] ' + str(repr_nullable(old)))
            print('\033[32m [NEW] ' + str(repr_nullable(new)))


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--field', choices=fields)
    parser.add_argument('-c', '--cache', action='store_true')
    args = parser.parse_args()

    if not args.cache:
        fetch_files()
    compare_versions(args.field)
