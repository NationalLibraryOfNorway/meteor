"""Simple script to run Meteor on a local file

usage: `python run_on_file.py /path/to/file.pdf \
   [-r </path/to/registry.db>] \
   [-g] [-l <language codes>]`
"""


import argparse
import json
from metadata_extract.meteor import Meteor
from metadata_extract.registry import PublisherRegistry


parser = argparse.ArgumentParser()
parser.add_argument('filename')
parser.add_argument('-r', '--registry')
parser.add_argument('-g', '--giella', action="store_true")
parser.add_argument('-l', '--langs')

args = parser.parse_args()

meteor = Meteor()

if args.registry:
    registry = PublisherRegistry(registry_file=args.registry)
    meteor.set_registry(registry)

if args.giella:
    import gielladetect  # pylint: disable=import-error
    langs = args.langs.split(',') if args.langs else None
    meteor.set_language_detection_method(
        lambda t: gielladetect.detect(t, langs=langs)
    )

r = meteor.run(args.filename)
print(json.dumps(r, indent=2, ensure_ascii=False))
