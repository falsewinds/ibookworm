from contextlib import contextmanager
from datetime import datetime, timedelta
import os
import sqlite3 as sql


'''-------------------------------------------------------------
SQLite
-------------------------------------------------------------'''

TRIGGER_FORMAT = """
CREATE TRIGGER [update_{table}_{field}]
AFTER UPDATE ON {table}
FOR EACH ROW
BEGIN
UPDATE {table} SET {field}=CURRENT_TIMESTAMP WHERE ROWID = old.ROWID;
END
"""

INDEX_FORMAT = """
CREATE INDEX {table}_{field}_index ON {table} ({field})
"""

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = "data"
DB_DIR = os.path.join(ROOT_DIR, DB_FOLDER)

class db_manager:
    def __init__(self):
        self.dir = DB_DIR

    @contextmanager
    def open(self, db : str):
        try:
            con = sql.connect(os.path.join(self.dir,db))
            cur = con.cursor()
            yield cur
            con.commit()
            cur.close()
        finally:
            con.close()

    def mkdirs(self, db : str):
        path = os.path.join(DB_FOLDER,db)
        folders = os.path.dirname(path)
        if not os.path.exists(folders):
            os.makedirs(folders)

    def exists(self, db : str):
        path = os.path.join(self.dir,db)
        return os.path.exists(path)

    def remove(self, db : str):
        path = os.path.join(self.dir,db)
        if os.path.exists(path):
            os.remove(path)

def get_db_path(user_id : str, repo_id : str):
    return os.path.join(user_id,repo_id+".db")

DBA = db_manager()

'''-------------------------------------------------------------
SQLite TimeStamp -> Local TimeZone
-------------------------------------------------------------'''

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TAIWAN_TIMEZONE = timedelta(hours=8)

def utc_to_local(utc_str : str):
    dt = datetime.strptime(utc_str, DATETIME_FORMAT)
    dt += TAIWAN_TIMEZONE
    return dt.strftime(DATETIME_FORMAT)

def local_now_to_utc(offset : timedelta = timedelta(0)):
    now = datetime.now() + offset - TAIWAN_TIMEZONE
    return now.strftime(DATETIME_FORMAT)

def is_past(utc_str : str):
    dt = datetime.strptime(utc_str, DATETIME_FORMAT)
    dt += TAIWAN_TIMEZONE
    now = datetime.now()
    return (dt < now)

'''-------------------------------------------------------------
Solve Data
-------------------------------------------------------------'''
def solve_data_into_fields(data : dict, fieldtypes : dict):
    fields = [v for v in data.keys() if v in fieldtypes.keys()]
    fields = [v for v in fields if isinstance(data[v],fieldtypes[v]) ]
    values = [data[k] for k in fields]
    return (fields, values)

def solve_data_into_update_sql(table : str,
    data : dict, fieldtypes : dict,
    key : str, key_val):
    fields, values = solve_data_into_fields(data,fieldtypes)
    values += [key_val]
    sql = (f"UPDATE {table} SET "
        + (",".join([f"{field}=?" for field in fields]))
        + f" WHERE {key}=?")
    return (sql, tuple(values))