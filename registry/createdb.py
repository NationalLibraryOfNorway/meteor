from bs4 import BeautifulSoup
import glob
import sqlite3
import mysql.connector
from decouple import config


def formatName(nametag, filename, record_id):

    ind1 = int(nametag['ind1'])
    if ind1 == 0:
        return None

    name_a = None
    sub_a = nametag.find_all('marc:subfield', {'code': 'a'})
    if (len(sub_a)) != 1:
        print(f'unexpected $a for {filename} / {record_id}, {len(sub_a)}')
        return None
    name_a = sub_a[0].next

    name_b = None
    sub_b = nametag.find_all('marc:subfield', {'code': 'b'})
    if sub_b:
        name_b = '. '.join([b.next for b in sub_b])

    if ind1 == 1:
        return name_b

    elif ind1 == 2:
        return f'{name_a}. {name_b}' if name_b else name_a

    print(f'ind1 has value {ind1} in {filename} / {record_id}')
    return None


def process_record(marcrecord, filename):

    recordId = marcrecord.find('marc:controlfield', {'tag': '001'}).next

    category = marcrecord.find('marc:datafield', {'tag': '901'})
    value = category.find('marc:subfield', {'code': 'a'})
    kat = value.next
    if kat != 'kat2' and kat != 'kat3':
        return None

    nametag = marcrecord.find('marc:datafield', {'tag': '110'})
    name = formatName(nametag, filename, recordId)
    if not name:
        return None

    variants = []
    variantTags = marcrecord.find_all('marc:datafield', {'tag': '410'})
    for variant in variantTags:
        formattedName = formatName(variant, filename, recordId)
        if not formattedName:
            continue
        variants.append(formattedName)

    return {
        'id': recordId,
        'name': name,
        'variants': variants,
        'category': int(kat[-1])
    }


def process_file(filename):

    with open(filename, 'r') as f:
        data = f.read()

    marcrecord = BeautifulSoup(data, 'html5lib')
    records = marcrecord.find_all('marc:record')
    entries = []
    for record in records:
        entry = process_record(record, filename)
        if entry:
            entries.append(entry)
    return entries


sqlite_file = config("REGISTRY_FILE", None)
db_host = config("REGISTRY_HOST", None)
db_user = config("REGISTRY_USER", None)
db_database = config("REGISTRY_DATABASE", None)
db_password = config("REGISTRY_PASSWORD", None)

table_schema = "id LONG, name TEXT, standard TINYINT, category TINYINT"
if sqlite_file:
    connection = sqlite3.connect(sqlite_file, isolation_level=None)
    name_index = "LOWER(name)"
    values = "?,?,?,?"
else:
    connection = mysql.connector.connect(host=db_host,
                                         user=db_user,
                                         database=db_database,
                                         password=db_password,
                                         autocommit=True)
    table_schema += ", lower_name TEXT GENERATED ALWAYS AS (LOWER(name)) PERSISTENT"
    name_index = "lower_name"
    values = "%s,%s,%s,%s,default"

cursor = connection.cursor()

cursor.execute("DROP TABLE IF EXISTS organizations_new")
cursor.execute(f"CREATE TABLE organizations_new({table_schema})")

cursor.execute(f"CREATE TABLE IF NOT EXISTS organizations({table_schema})")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_org_id ON organizations(id)")
cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_org_name ON organizations({name_index})")

files = sorted(glob.glob('output/marc_*.xml'))

print(f"Starting working on {len(files)} files")

query = f"INSERT INTO organizations_new VALUES({values})"

for filename in files:
    entries = process_file(filename)
    new_values = []
    for e in entries:
        new_values.append([int(e['id']), str(e['name']), 1, str(e['category'])])
        for v in e['variants']:
            new_values.append([int(e['id']), str(v), 0, str(e['category'])])
    cursor.executemany(query, new_values)
    print(f"File {filename} added")

print("All files added!")

cursor.execute("DELETE FROM organizations")
cursor.execute("INSERT INTO organizations(id, name, standard, category) " +
               "SELECT id, name, standard, category FROM organizations_new")
cursor.execute("DROP TABLE organizations_new")

cursor.close()
connection.close()
