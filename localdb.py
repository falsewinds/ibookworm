from appconfig import cache, TIMEOUT_DAY
from globaldb import get_member_name, get_repository_name
import json
from sqlite_lib import DBA, TRIGGER_FORMAT, INDEX_FORMAT, utc_to_local, get_db_path


'''-------------------------------------------------------------
Local Database : Repository
 - create_repository(user,repo)
 - save_info(user,repo,key,value)
-------------------------------------------------------------'''
CREATE_TABLE_toc = """
CREATE TABLE toc (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    parent      INTEGER DEFAULT NULL,
    ordinal     INTEGER DEFAULT NULL,
    doc_id	    INT DEFAULT NULL,
    title	    TEXT NOT NULL DEFAULT '',
    editor      TEXT NOT NULL,
    updated     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (parent) REFERENCES toc(id),
FOREIGN KEY (ordinal) REFERENCES toc(id),
FOREIGN KEY (doc_id) REFERENCES doc(id)
);"""

CREATE_TABLE_doc = """
CREATE TABLE doc (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL DEFAULT 'unnamed',
    type        TEXT NOT NULL DEFAULT 'article',
    version     INTEGER NOT NULL DEFAULT 0,
    metadata    TEXT NOT NULL DEFAULT '{}',
    content     BLOB NOT NULL,
    created     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

CREATE_TABLE_ver = """
CREATE TABLE ver (
    doc_id      INTEGER DEFAULT NULL,
    version     INTEGER NOT NULL DEFAULT 0,
    changes     TEXT NOT NULL DEFAULT '{}',
    editor_id   VARCHAR(32) NOT NULL,
    saved       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY (doc_id) REFERENCES doc(id),
PRIMARY KEY (doc_id, version)
);"""

CREATE_TABLE_inf = """
CREATE TABLE inf (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    inf_key     TEXT NOT NULL,
    inf_val     TEXT NOT NULL
);"""

def create_repository(user, repo):
    db = get_db_path(user,repo)
    DBA.mkdirs(db)
    with DBA.open(db) as cur:
        cur.execute(CREATE_TABLE_toc)
        cur.execute(TRIGGER_FORMAT.format(table="toc",field="updated"))
        cur.execute(INDEX_FORMAT.format(table="toc",field="doc_id"))
        cur.execute(CREATE_TABLE_doc)
        cur.execute(TRIGGER_FORMAT.format(table="doc",field="updated"))
        cur.execute(CREATE_TABLE_ver)
        cur.execute(TRIGGER_FORMAT.format(table="ver",field="saved"))
        cur.execute(INDEX_FORMAT.format(table="ver",field="doc_id"))
        cur.execute(CREATE_TABLE_inf)
        cur.execute("""
            INSERT INTO inf (inf_key,inf_val)
            VALUES (?,CURRENT_TIMESTAMP)
            """,("CREATE_DATETIME",))

def save_info(user, repo, key, val):
    db = get_db_path(user,repo)
    with DBA.open(db) as cur:
        cur.execute("""
            INSERT INTO inf (inf_key,inf_val)
            VALUES (?,?)
            """,(key,val))

'''-------------------------------------------------------------
Local Database : ToC & DOC (VER)
 + list_toc(user,repo) -> []
 = update_toc(user,repo,data)
 = hide_toc(user,repo,hide)
 - create_doc(user,repo,title,type,meta,data) -> doc_id
 - update_doc(user,repo,doc_id,data)
 = delete_doc(user,repo,doc_id)
 + read_doc(user,repo,doc_id)
 = insert_doc_meta(user,repo,doc_id,new_metadata)
 = remove_doc_meta(user,repo,doc_id,remove_keys)
-------------------------------------------------------------'''

TOC_KEYS = [ "sn", "parent", "ordinal", "doc_id", "title", "editor", "updated" ]
@cache.memoize(timeout=TIMEOUT_DAY)
def list_toc(user, repo):
    db = get_db_path(user,repo)
    rows = []
    with DBA.open(db) as cur:
        cur.execute("SELECT * FROM toc ORDER BY parent ASC, ordinal ASC, id ASC")
        for row in cur.fetchall():
            rows.append({ k: row[i] for i,k in enumerate(TOC_KEYS) })
    return {
        "id": repo,
        "name": get_repository_name(repo),
        "rows": rows
    }

"""
doc.type:
 - article : simple richtext { "richtext": true/false, "lines": [ STRING ] }
 - translation : simple text { "language": STRING, "lines": [ STRING ] }
 - map : { "width": INT, "height": INT, "center": POINT, "regions": { ... } }
 - glossary : like article, but serve for keyword purpose.
 - chronicle : { "calendar": { "format": (calendar format string) }, "events": [ EVENT ] }
 - relation : { "character": [ STRING ], "relations": [ RELATION ] }
"""
def create_doc(user, repo, title, type, meta, data):
    db = get_db_path(user,repo)
    with DBA.open(db) as cur:
        cur.execute("""
            INSERT INTO doc (title,type,metadata,content)
            VALUES (?,?,?,?)
            """,(title,type,json.dumps(meta),data))
        cur.execute("SELECT id FROM doc WHERE ROWID=?",(cur.lastrowid,))
        doc_id = cur.fetchone()[0]
        user_name = get_member_name(user)
        cur.execute("""
            INSERT INTO toc (doc_id,title,editor)
            """,(doc_id,title,user_name))
        cur.execute("""
            INSERT INTO ver (doc_id,editor_id)
            """,(doc_id,user))
    cache.delete_memoized(list_toc,db)
    cache.delete_memoized(read_doc,db,doc_id)
    return doc_id

def update_doc(user, repo, doc_id, data):
    doc_val = []
    doc_sql = "UPDATE doc SET"
    toc_val = []
    toc_sql = "UPDATE toc SET"
    if "title" in data:
        doc_val.append(data["title"])
        doc_sql += " title=?,"
        toc_val.append(data["title"])
        toc_sql += " title=?,"
    if "type" in data:
        doc_val.append(data["type"])
        doc_sql += " type=?,"
    doc_sql += " version=version+1,"
    if "metadata" in data:
        doc_val.append(json.dumps(data["metadata"]))
        doc_sql += " metadata=?,"
    if "content" in data:
        doc_val.append(data["content"])
        doc_sql += " content=?"
    doc_sql += " WHERE id=?"
    doc_val.append(doc_id)
    doc_sql += " editor=? WHERE doc_id=?"
    toc_val.append(get_member_name(user))
    toc_val.append(doc_id)
    changes = "{}"
    if "changes" in data:
        changes = json.dumps(data["changes"])
    db = get_db_path(user,repo)
    with DBA.open(db) as cur:
        cur.execute(doc_sql,tuple(doc_val))
        cur.execute("SELECT version FROM doc WHERE ROWID=?",(cur.lastrowid,))
        version = cur.fetchone()[0]
        cur.execute(toc_sql,tuple(toc_val))
        cur.execute("""
            INSERT INTO ver (doc_id,version,changes,editor_id)
            """,(doc_id,version,changes,user))
    cache.delete_memoized(list_toc,db)
    cache.delete_memoized(read_doc,db,doc_id)
    return doc_id

@cache.memoize(timeout=TIMEOUT_DAY)
def read_doc(user, repo, doc_id):
    db = get_db_path(user,repo)
    with DBA.open(db) as cur:
        cur.execute("SELECT * FROM doc WHERE id=?",(doc_id,))
        row = cur.fetchone()
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