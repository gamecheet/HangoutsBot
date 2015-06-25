import sqlite3

_database_file = None
_imageids_db = 'image_ids.db'

class DatabaseNotInitializedError(BaseException):
    pass


def setDatabase(db):
    global _database_file
    _database_file = db
    _init_tables()


def _init_table(table_name, table_def, cursor):
    cursor.execute(
      "SELECT name FROM sqlite_master WHERE type='table' AND name='{0}'"
        .format(table_name)
    )
    if not cursor.fetchone():
        cursor.execute(table_def)

def _init_tables():
    imageids_db = sqlite3.connect(_imageids_db)
    cursor = imageids_db.cursor()

    image_id_def = '''\
CREATE TABLE image_id (
  db_id     INTEGER UNIQUE,
  google_id TEXT
)
'''
    _init_table('image_id', image_id_def, cursor)

    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        karma_def = "CREATE TABLE karma (user_id text, karma integer)"
        _init_table('karma', karma_def, cursor)

        reminders_def = "CREATE TABLE reminders (conv_id text, message text, timestamp integer)"
        _init_table('reminders', reminders_def, cursor)

        alias_def = '''\
CREATE TABLE alias (
  id        INTEGER PRIMARY KEY ASC,
  alias     TEXT UNIQUE
)
'''
        _init_table('alias', alias_def, cursor)

        image_def = '''\
CREATE TABLE image (
  id        INTEGER PRIMARY KEY ASC,
  url       TEXT,
  filename  TEXT
);
'''
        _init_table('image', image_def, cursor)

        xref_image_alias_def = '''\
CREATE TABLE xref_image_alias (
  id        INTEGER PRIMARY KEY ASC,
  image_id  INTEGER,
  alias_id  INTEGER,
  FOREIGN KEY(image_id) REFERENCES image(id),
  FOREIGN KEY(alias_id) REFERENCES alias(id),
  UNIQUE(image_id, alias_id)
)
'''

        _init_table('xref_image_alias', xref_image_alias_def, cursor)

        database.commit()
        cursor.close()
        database.close()
    else:
        raise DatabaseNotInitializedError()


def get_value_by_user_id(table, user_id, conv_id=None):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()
        if conv_id:
            cursor.execute("SELECT * FROM %s WHERE user_id = ? AND conv_id = ?" % table, (user_id, conv_id))
        else:
            cursor.execute("SELECT * FROM %s WHERE user_id = ?" % table, (user_id,))
        return cursor.fetchone()

    else:
        raise DatabaseNotInitializedError()


def get_values_by_user_id(table, user_id, conv_id=None):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()
        if conv_id:
            cursor.execute("SELECT * FROM %s WHERE user_id = ? AND conv_id = ?" % table, (user_id, conv_id))
        else:
            cursor.execute("SELECT * FROM %s WHERE user_id = ?" % table, (user_id,))
        return cursor.fetchall()

    else:
        raise DatabaseNotInitializedError()


def set_value_by_user_id(table, user_id, keyword, value, conv_id=None):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()
        if conv_id:
            result = get_value_by_user_id(table, user_id, conv_id)
            if result:
                cursor.execute("UPDATE %s SET %s = ? WHERE user_id = ? and conv_id = ?" % (table, keyword),
                               (keyword, value, user_id, conv_id))
            else:
                cursor.execute("INSERT INTO %s VALUES (?, ?, ?)" % table, (user_id, conv_id, value))
        else:
            result = get_value_by_user_id(table, user_id, conv_id)
            if result:
                cursor.execute("UPDATE %s SET %s = ? WHERE user_id = ?" % (table, keyword), (value, user_id))
            else:
                cursor.execute("INSERT INTO %s VALUES (?, ?)" % table, (user_id, value))
        database.commit()
    else:
        raise DatabaseNotInitializedError()

def get_database():
    return _database_file

def get_row_dict(table, id):
    con = sqlite3.connect(_database_file)
    with con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM %s WHERE id = ?" % table, id)
        row = cur.fecthone()
    return row

def get_image(id):
    return get_row_dict('image', id)

def insert_row_dict(dict):
    con = sqlite3.connect(_database_file)
#    with con:
#        con.execute("INSERT INTO %s

class Image:
    def __init__(self, id=None):
        if id:
            self.id = id
            if _database_file:
                database = sqlite3.connect(_database_file)
                cursor = database.cursor()
                table = 'image'
                cursor.execute("SELECT * FROM %s WHERE id = ?" % table, id)
                image = cursor.fetchone()
                self.url = image['url']
                self.filename = image['filename']
                #self.group = 

            else:
                raise DatabaseNotInitializedError()
        else:
            self.id = None

    def update():
        if _database_file:
            database = sqlite3.connect(_database_file)
            cursor = database.cursor()
            cursor.execute("UPDATE image SET url = ?, filename = ?, google_id = ? WHERE id = ?", (url, filename, google_id))
            database.commit()
        else:
            raise DatabaseNotInitializedError()

    def insert():
        if _database_file:
            database = sqlite3.connect(_database_file)
            cursor = database.cursor()
            cursor.execute("INSERT INTO image (url, filename, google_id) VALUES (?, ?, ?)", (url, filename, google_id))
            database.commit()
        else:
            raise DatabaseNotInitializedError()

def get_list_of_aliases():
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        cursor.execute("""\
SELECT alias
FROM alias
""")
        result = cursor.fetchall()
        if result is None or not result:
            return None
        else:
            return [x[0] for x in result]

def get_column_for_alias(column, alias):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        if column == 'google_id':
            cursor.execute("""\
ATTACH DATABASE ? AS image_id
""", (_imageids_db,))
            cursor.execute("""\
SELECT image_id.google_id
FROM xref_image_alias
JOIN image ON xref_image_alias.image_id = image.id
JOIN alias ON xref_image_alias.alias_id = alias.id
JOIN image_id ON xref_image_alias.image_id = image_id.db_id
WHERE alias.alias = ?
""".format(column), (alias,))

        else:
            cursor.execute("""\
SELECT image.{}
FROM xref_image_alias
JOIN image ON xref_image_alias.image_id = image.id
JOIN alias ON xref_image_alias.alias_id = alias.id
WHERE alias.alias = ?
""".format(column), (alias,))
        result = cursor.fetchall()
        if result is None or not result:
            return None
        else:
            return [x[0] for x in result]

def get_urls_for_alias(alias):
    return get_column_for_alias('url', alias)

def get_filenames_for_alias(alias):
    return get_column_for_alias('filename', alias)

def get_imageids_for_alias(alias):
    return get_column_for_alias('google_id', alias)

def get_imageid_for_column(column, column_data):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        cursor.execute("""\
ATTACH DATABASE ? AS image_id
""", (_imageids_db,))

        cursor.execute("""\
SELECT image_id.google_id
FROM image_id.image_id
WHERE image_id.db_id = (SELECT id FROM image WHERE {} = ?)
""".format(column), (column_data,))
        result = cursor.fetchone()
        return None if result is None else result[0]

def get_imageid_for_url(url):
    return get_imageid_for_column('url', url)

def get_imageid_for_filename(filename):
    return get_imageid_for_column('filename', filename)

def set_imageid_for_column(column, column_data, google_id):
    print("setting imageid for column")
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        cursor.execute("""\
ATTACH DATABASE ? AS image_id
""", (_imageids_db,))

        cursor.execute('''\
INSERT INTO image({})
SELECT ?
WHERE NOT EXISTS (SELECT 1 FROM image WHERE {} = ?)
'''.format(column, column), (column_data, column_data))

        try:
            cursor.execute("""\
INSERT INTO image_id(db_id, google_id)
SELECT (SELECT id FROM image WHERE {} = ?), ?
""".format(column, column), (column_data, google_id))
        except sqlite3.IntegrityError:
            pass

        database.commit()

def set_imageid_for_url(url, google_id):
    set_imageid_for_column('url', url, google_id)

def set_imageid_for_filename(filename, google_id):
    set_imageid_for_column('filename', filename, google_id)

def set_alias_for_column(column, column_data, alias):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        cursor.execute('''\
INSERT INTO alias(alias)
SELECT ?
WHERE NOT EXISTS (SELECT 1 FROM alias WHERE alias = ?)
''', (alias, alias))

        cursor.execute('''\
INSERT INTO image({})
SELECT ?
WHERE NOT EXISTS (SELECT 1 FROM image WHERE {} = ?)
'''.format(column, column), (column_data, column_data))

        try:
            cursor.execute('''\
INSERT INTO xref_image_alias(image_id, alias_id)
SELECT image.id, (SELECT id FROM alias WHERE alias = ?)
FROM   image
WHERE  image.{} = ?
'''.format(column), (alias, column_data))
        except sqlite3.IntegrityError:
            pass

        database.commit()

def set_alias_for_url(url, alias):
    set_alias_for_column('url', url, alias)

def set_alias_for_filename(filename, alias):
    set_alias_for_column('filename', filename, alias)

