#!/bin/bash

echo "Downloading latest BIBSYS export..."
curl -s "https://authority.bibsys.no/authority/rest/functions/v2/exports" | jq .'path' | xargs wget -O export.zip

echo "Unzipping..."
unzip -q export.zip
rm export.zip
gunzip *.xml.gz

mkdir output

echo "Splitting files and selecting records..."
for f in *.xml; do
    echo "  Splitting ${f}"
    fileindex=${f:18:3}
    csplit -s -b %04d -f output/marc_${fileindex}_ $f /\<marc:record/ '{*}'
    grep -L 'marc:datafield tag="110"' output/marc_${fileindex}_* | xargs rm
    cat output/marc_${fileindex}_* > output/marc_${fileindex}.xml
    rm output/marc_${fileindex}_*
done;

rm *.xml
rm metadata.json

source ../.env

echo "Populating database..."
python3 -u createdb.py

echo "Done!"
