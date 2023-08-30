# METEOR - Metadata extraction from PDF reports

A web service to extract metadata from a digital-native PDF report.

### Start the program

Requires Python 3.11

First time:

```
git clone git@git.nb.no:tekst/metadata_extraction.git
cd metadata_extraction
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy and edit the env file to set DIMO_FOLDER to the local path used in DIMO file server.

```
cp .env.example .env
```

Finally, start the flask app (debug mode optional, reloads service automatically after file change):

```
uvicorn main:app --reload --port=5000
```

Then open http://127.0.0.1:5000

or use curl

```
curl -F fileInput=@/path/to/file.pdf http://127.0.0.1:5000/json

curl -d fileUrl=https://www.link.to/report.pdf http://127.0.0.1:5000/json
```

### Local development

After installing requirements, run `pre-commit install`. This adds a pre-commit PEP8 compliance check.

### Installing the python module

In order to install the core module `metadata_extract`, simply run:

```
python3 -m pip install .
```

Usage:

```
>>> from metadata_extract import meteor
>>> m = meteor.Meteor()
>>> results = m.run('/path/to/file.pdf')
```

### Extracted fields

For now, the program attempts to identify:

- ISBN
- ISSN
- Title
- Publisher
- Publication year
- Language
- Authors
- Publication type

### Norwegian Authority File

Publisher names can be looked for in the [Norwegian Authority File](https://bibsys-almaprimo.hosted.exlibrisgroup.com/primo-explore/search?vid=AUTREG&lang=en_US).

To build a database from the registry's API, define the environment variables as described in `.env.example` then run `script.sh` in the `registry` directory.

The resulting database will contain all entries of type corporations (MARC field 110 is present) and of quality level kat2 and kat3 (in MARC field 901).
