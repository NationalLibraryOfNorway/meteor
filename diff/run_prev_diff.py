"""Diff-script: write previous Meteor results for all evaluation files

This script has to be executed with the previous version of Meteor, i.e.
without the new feature being developed.
"""


# pylint: disable=wrong-import-position, wrong-import-order

import json
import os
import sys
from decouple import config

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from metadata_extract.meteor import Meteor  # noqa: E402


# pylint: disable=broad-exception-caught, duplicate-code
def create_previous_version_json() -> None:
    meteor = Meteor()
    response_data = []
    pdf_folder_path = config('DIFF_FILES_FOLDER')
    pdf_files = os.listdir(pdf_folder_path)

    for file in pdf_files:
        print(f"Processing file {file}")
        try:
            response = meteor.run(pdf_folder_path + "/" + file)
        except Exception as ex:
            print(f"Error while processing file {file}: {ex}")
            continue
        result = {
            'doc_id': int(file.split(".")[0]),
            'metadata': response
        }
        response_data.append(result)

    with open('diff/previous_results.json', 'w', encoding="UTF-8") as previous_results_file:
        json.dump(response_data, previous_results_file, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    create_previous_version_json()
