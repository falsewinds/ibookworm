from contextlib import contextmanager
from datetime import datetime, timedelta
import json
import os
import sqlite3 as sql

CREATE_TABLE_toc = """
CREATE TABLE toc (
    id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    parent  INTEGER DEFAULT NULL,
    after   INTEGER DEFAULT NULL,
    doc_id	INT DEFAULT NULL,
    title	  TEXT NOT NULL DEFAULT '',
    editor  TEXT NOT NULL,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (parent) REFERENCES toc(id),
FOREIGN KEY (after) REFERENCES toc(id),
FOREIGN KEY (doc_id) REFERENCES doc(id)
);"""

CREATE_TABLE_doc = """
CREATE TABLE doc (
    id        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    title     TEXT NOT NULL DEFAULT 'unnamed',
    type      TEXT NOT NULL DEFAULT 'article',
    version   INTEGER NOT NULL DEFAULT 0,
    metadata  TEXT NOT NULL DEFAULT '{}',
    content   BLOB NOT NULL,
    created   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

"""
doc.type:
 - article : simple richtext { "richtext": true/false, "lines": [ STRING ] }
 - translation : simple text { "language": STRING, "lines": [ STRING ] }
 - map : { "width": INT, "height": INT, "center": POINT, "regions": { ... } }
 - glossary : like article, but serve for keyword purpose.
 - chronicle : { "calendar": { "format": (calendar format string) }, "events": [ EVENT ] }
 - relation : { "character": [ STRING ], "relations": [ RELATION ] }
"""

CREATE_TABLE_ver = """
CREATE TABLE ver (
    doc_id    INTEGER DEFAULT NULL,
    version   INTEGER NOT NULL DEFAULT 0,
    changes   TEXT NOT NULL DEFAULT '{}',
    editor_id INTEGER NOT NULL,
    saved     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (doc_id) REFERENCES doc(id),
PRIMARY KEY (doc_id, version)
);"""

CREATE_TABLE_inf = """
CREATE TABLE inf (
    id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    inf_key TEXT NOT NULL,
    inf_val TEXT NOT NULL
);"""

TRIGGER_FORMAT = """
CREATE TRIGGER [update_{table}_{field}]
AFTER UPDATE ON {table}
FOR EACH ROW
BEGIN
UPDATE {table} SET {field}=CURRENT_TIMESTAMP WHERE ActionId = old.ActionId;
END
"""

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(ROOT_DIR, "data")
print(DB_DIR)

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

DBA = db_manager()

def create_repository(db : str):
    with DBA.open(db) as cur:
        cur.execute(CREATE_TABLE_toc)
        cur.execute(CREATE_TABLE_doc)
        cur.execute(CREATE_TABLE_ver)
        cur.execute(CREATE_TABLE_inf)
        cur.execute(TRIGGER_FORMAT.format(table="toc",field="updated"))
        cur.execute(TRIGGER_FORMAT.format(table="doc",field="updated"))
        cur.execute(TRIGGER_FORMAT.format(table="ver",field="saved"))
        cur.execute("""
            INSERT INTO inf (inf_key,inf_val)
            VALUES (?,CURRENT_TIMESTAMP)
            """,("CREATE_DATETIME",))

def create_doc(db : str, title : str, type : str, meta : dict, data : str):
    with DBA.open(db) as cur:
        cur.execute("""
            INSERT INTO doc (title,type,metadata,content)
            VALUES (?,?,?,?)
            """,(title,type,json.dumps(meta),data))
        doc_id = cur.lastrowid
    return doc_id

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TAIWAN_TIMEZONE = timedelta(hours=8)
def utc_to_local(dt_str : str):
    dt = datetime.strptime(dt_str, DATETIME_FORMAT)
    dt += TAIWAN_TIMEZONE
    return dt.strftime(DATETIME_FORMAT)

def read_doc(db : str, doc_id : int):
    with DBA.open(db) as cur:
        cur.execute("SELECT * FROM doc WHERE id=?",(doc_id,))
        row = cur.fetchone()
        print(row)
    return {
        "id": row[0],
        "tilte": row[1],
        "type": row[2],
        "version": row[3],
        "metadata": json.loads(row[4]),
        "content": row[5],
        "created": utc_to_local(row[6]),
        "updated": utc_to_local(row[7]),
    }