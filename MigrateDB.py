import os
import json
import sqlite3
from Core.Util import UtilDB

_database_file = 'database.db'

def migrate_imageids():
    imageids_filename = 'imageids.json'
    imageids = json.loads(open(imageids_filename, encoding='utf-8').read(), encoding='utf-8')

    database = sqlite3.connect(_database_file)
    cursor = database.cursor()

    imageids_list = list(imageids.items())
    print(imageids_list)
    cursor.executemany(
        "INSERT INTO image(url, google_id) VALUES (?, ?)", imageids_list
    )

    database.commit()
    cursor.close()
    database.close()

def migrate_image_aliases():
    aliases_filename = 'image_aliases.json'
    aliases = json.loads(open(aliases_filename, encoding='utf-8').read(), encoding='utf-8')
    
    database = sqlite3.connect(_database_file)
    cursor = database.cursor()

    for alias in sorted(aliases.keys()):
        print(alias)
        cursor.execute("INSERT INTO alias(alias) VALUES (?)", (alias,))
        alias_row_id = cursor.lastrowid

        alias_list = aliases.get(alias)
        if alias_list is not None:
            if isinstance(alias_list, str):
                alias_list = [alias_list]
            for url in alias_list:
                # insert into image if doesn't exist
                cursor.execute('''\
INSERT INTO image(url)
SELECT ?
WHERE NOT EXISTS (SELECT 1 FROM image WHERE url = ?)
''', (url, url))

                cursor.execute('''\
INSERT INTO xref_image_alias(image_id, alias_id)
SELECT image.id, ?
FROM   image
WHERE  image.url = ?
''', (alias_row_id, url))

    database.commit()
    cursor.close()
    database.close()


def migrate_ezhiks():
    imageids_filename = 'ezhiks.json'
    imageids = json.loads(open(imageids_filename, encoding='utf-8').read(), encoding='utf-8')

    database = sqlite3.connect(_database_file)
    cursor = database.cursor()

    for filename in sorted(imageids.keys()):
        oldfilename = filename
        filename = os.path.join('ezhik', filename)
        cursor.execute('''\
INSERT INTO image(filename, google_id)
VALUES (?, ?)
''', (filename, imageids[oldfilename]))

        alias = 'ezhik'

        cursor.execute('''\
INSERT INTO alias(alias)
SELECT ?
WHERE NOT EXISTS (SELECT 1 FROM alias WHERE alias = ?)
''', (alias, alias))

        alias_row_id = cursor.lastrowid

        cursor.execute('''\
INSERT INTO image(filename)
SELECT ?
WHERE NOT EXISTS (SELECT 1 FROM image WHERE filename = ?)
''', (filename, filename))

        try:
            cursor.execute('''\
INSERT INTO xref_image_alias(image_id, alias_id)
SELECT image.id, (SELECT id FROM alias WHERE alias = ?)
FROM   image
WHERE  image.filename = ?
''', (alias, filename))
        except sqlite3.IntegrityError:
            pass

    database.commit()
    cursor.close()
    database.close()


#migrate_imageids()        
#migrate_image_aliases()
migrate_ezhiks()
