import sqlite3

_database_file = None


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
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        karma_def = "CREATE TABLE karma (user_id text, karma integer)"
        _init_table('karma', karma_def, cursor)

        reminders_def = "CREATE TABLE reminders (conv_id text, message text, timestamp integer)"
        _init_table('reminders', reminders_def, cursor)

        image_group_def = '''\
CREATE TABLE image_group (
  id        INTEGER PRIMARY KEY ASC,
  name      TEXT
)
'''
        _init_table('image_group', image_group_def, cursor)

        alias_def = '''\
CREATE TABLE alias (
  id        INTEGER PRIMARY KEY ASC,
  alias     TEXT
)
'''
        _init_table('alias', alias_def, cursor)

        image_def = '''\
CREATE TABLE image (
  id        INTEGER PRIMARY KEY ASC,
  url       TEXT,
  filename  TEXT,
  google_id TEXT,
  group_id  INTEGER,
  FOREIGN KEY(group_id) REFERENCES image_group(id)
);
'''
        _init_table('image', image_def, cursor)

        xref_image_alias_def = '''\
CREATE TABLE xref_image_alias (
  id        INTEGER PRIMARY KEY ASC,
  image_id  INTEGER,
  alias_id  INTEGER,
  FOREIGN KEY(image_id) REFERENCES image(id),
  FOREIGN KEY(alias_id) REFERENCES alias(id)
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
SELECT alias.alias
FROM xref_image_alias
JOIN alias ON xref_image_alias.alias_id = alias.id;
""")
        result = cursor.fetchall()
        if result is None or not result:
            return None
        else:
            return [x[0] for x in result]

def get_urls_for_alias(alias):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        cursor.execute("""\
SELECT image.url
FROM xref_image_alias
JOIN image ON xref_image_alias.image_id = image.id
JOIN alias ON xref_image_alias.alias_id = alias.id
WHERE alias.alias = ?
""", (alias,))
        result = cursor.fetchall()
        if result is None or not result:
            return None
        else:
            return [x[0] for x in result]

def get_filenames_for_alias(alias):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        cursor.execute("""\
SELECT image.filename
FROM xref_image_alias
JOIN image ON xref_image_alias.image_id = image.id
JOIN alias ON xref_image_alias.alias_id = alias.id
WHERE alias.alias = ?
""", (alias,))
        result = cursor.fetchall()
        if result is None or not result:
            return None
        else:
            return [x[0] for x in result]

def get_imageid_for_url(url):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        cursor.execute("""\
SELECT google_id
FROM image
WHERE url = ?
""", (url,))
        result = cursor.fetchone()
        return result[0]
        #return None if result is None else result[0]

def get_imageid_for_filename(filename):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        cursor.execute("""\
SELECT google_id
FROM image
WHERE filename = ?
""", (filename,))
        result = cursor.fetchone()
        return result[0]

def set_imageid_for_url(url, google_id):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        cursor.execute("""\
UPDATE image
SET google_id = ?
WHERE url = ?
""", (google_id, url))

        database.commit()

def set_imageid_for_filename(filename, google_id):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        cursor.execute('''\
INSERT INTO image(filename)
SELECT ?
WHERE NOT EXISTS (SELECT 1 FROM image WHERE filename = ?)
''', (filename, filename))

        cursor.execute("""\
UPDATE image
SET google_id = ?
WHERE filename = ?
""", (google_id, filename))

        database.commit()

def set_alias_for_url(url, alias):
    if _database_file:
        database = sqlite3.connect(_database_file)
        cursor = database.cursor()

        cursor.execute("INSERT INTO alias(alias) VALUES (?)", (alias,))
        alias_row_id = cursor.lastrowid

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

