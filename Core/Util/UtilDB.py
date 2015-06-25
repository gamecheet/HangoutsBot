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

        group_def = '''\
CREATE TABLE group (
  id        INTEGER PRIMARY KEY ASC,
  name      TEXT
)
'''
        _init_table('group', group_def, cursor)

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
  google_id TEXT
  FOREIGN KEY(group_id) REFERENCES group(id)
);
'''
        _init_table('image', image_def, cursor)

        image_alias_def = '''\
CREATE TABLE image_alias (
  id        INTEGER PRIMARY KEY ASC,
  FOREIGN KEY(image_id) REFERENCES image(id),
  FOREIGN KEY(alias_id) REFERENCES alias(id)
)
'''

        _init_table('image_alias', image_alias_def, cursor)

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



