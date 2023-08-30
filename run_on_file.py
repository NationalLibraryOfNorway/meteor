"""Simple script to run Meteor on a local file

usage: `python run_on_file.py /path/to/file.pdf [-r </path/to/registry.db>]`
"""


import argparse
import json
from metadata_extract.meteor import Meteor
from metadata_extract.registry import PublisherRegistry


parser = argparse.ArgumentParser()
parser.add_argument('filename')
parser.add_argument('-r', '--registry')
args = parser.parse_args()

meteor = Meteor()

if args.registry:
    registry = PublisherRegistry(registry_file=args.registry)
    meteor.set_registry(registry)

r = meteor.run(args.filename)
print(json.dumps(r, indent=2, ensure_ascii=False))
