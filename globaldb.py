from appconfig import cache, TIMEOUT_DAY
import boto3
import hashlib
import json
from localdb import DBA, TRIGGER_FORMAT, INDEX_FORMAT, get_db_path
import os
from time import time

GDB_PATH = None
FAKE_ONLY_TOKEN = "the-fake-given-access-token"


@cache.memoize(timeout=TIMEOUT_DAY)
def get_member_name(user : str):
    with DBA.open(GDB_PATH) as cur:
        cur.execute("SELECT name FROM members WHERE id=?",(user,))
        row = cur.fetchone()
        if row is None:
            return None
        return row[0]

@cache.memoize(timeout=TIMEOUT_DAY)
def get_repository_id(id_or_alias : str):
    with DBA.open(GDB_PATH) as cur:
        cur.execute("SELECT id FROM repositories WHERE id=? OR alias=?",
            (id_or_alias,id_or_alias))
        row = cur.fetchone()
        if row is None:
            return None
        return row[0]

@cache.memoize(timeout=TIMEOUT_DAY)
def get_repository_name(id : str):
    with DBA.open(GDB_PATH) as cur:
        cur.execute("SELECT name FROM repositories WHERE id=?",(id,))
        row = cur.fetchone()
        if row is None:
            return None
        return row[0]


'''
GlobalDB Functions:
    initialize(cfg : dict)
    get_token(user, pwd) -> (T/F,token/error message)
    is_token_expired(user, token) -> (T/F,new token|None/None)
    set_token_expired(user, token)
    get_user_data(user)
'''

def initialize(cfg : dict):
    global GDB_PATH
    db_name = "global"
    if "filename" in cfg:
        db_name = cfg["filename"]
    GDB_PATH = db_name + ".db"
    # not initialize need if db is exists
    if DBA.exists(GDB_PATH):
        return
    # CREATE TABLE
    with DBA.open(GDB_PATH) as cur:
        cur.execute("""
CREATE TABLE repositories (
    id          VARCHAR(32) NOT NULL PRIMARY KEY,
    alias       VARCHAR(16),
    name        TEXT NOT NULL,
    size        INTEGER NOT NULL DEFAULT 0,
    view_rank   INTEGER NOT NULL DEFAULT 0,
    owner_id    VARCHAR(32) NOT NULL,
    owner_name  TEXT,
    since       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
UNIQUE (alias),
FOREIGN KEY (owner_id) REFERENCES members(id)
);""")
        cur.execute(TRIGGER_FORMAT.format(table="repositories",field="updated"))
        cur.execute("""
CREATE TABLE members (
    id          VARCHAR(32) NOT NULL PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE,
    name        TEXT,
    layout      TEXT NOT NULL DEFAULT '{}',
    bookmarks   TEXT NOT NULL DEFAULT '{}',
    space       INTEGER NOT NULL DEFAULT 0,
    since       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);""")
        cur.execute("""
CREATE TABLE permissions (
    repository  VARCHAR(32) NOT NULL,
    member      VARCHAR(32) NOT NULL,
    supervisor  VARCHAR(32),
    permission  INTEGER NOT NULL DEFAULT 1,
PRIMARY KEY (repository,member),
FOREIGN KEY (repository) REFERENCES repositories(id),
FOREIGN KEY (member) REFERENCES members(id),
FOREIGN KEY (supervisor) REFERENCES members(id)
);""")
        cur.execute(INDEX_FORMAT.format(table="permissions",field="repository"))
        cur.execute(INDEX_FORMAT.format(table="permissions",field="member"))
        # TABLE tokens is not used when using Cognito
#         cur.execute("""
# CREATE TABLE tokens (
#     token       VARCHAR(32) NOT NULL PRIMARY KEY,
#     member      VARCHAR(32) NOT NULL,
#     secret      VARCHAR(32) NOT NULL,
#     expired_at  TIMESTAMP NOT NULL,
#     ip_addr     TEXT,
#     agent       TEXT,
# FOREIGN KEY (member) REFERENCES members(id)
# );""")

def get_token(user : str, pwd : str):
    # TODO: log-in using user & pwd
    return (True,FAKE_ONLY_TOKEN)
    #return (False,"Invalid Access")

def is_token_expired(user : str, token : str):
    # change to Cognito to check token
    if token == FAKE_ONLY_TOKEN:
        # renew token
        return (False,None)
    return (True,FAKE_ONLY_TOKEN)

def set_token_expired(user : str, token : str):
    # TODO: remove token from GlobalDB/Cognito
    pass

def get_user_data(user : str):
    with DBA.open(GDB_PATH) as cur:
        cur.execute("SELECT * FROM members WHERE id=?",(user,))
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "name": row[2],
            "layout": json.loads(row[3]),
            "bookmarks": json.load(row[4]),
            "space": row[5]
        }


def create_repository(user : str, title : str):
    display_name = get_member_name(user)
    stamped = ".".join([title,str(int(time()))])
    id = hashlib.md5(stamped.encode('utf-8')).hexdigest()
    with DBA.open(GDB_PATH) as cur:
        cur.execute("""
            INSERT INTO repositories (id,name,owner_id,owner_name)
            VALUES (?,?,?,?)
            """,(id,title,user,display_name))
        cur.execute("""
            INSERT INTO permissions (repository,member,permission)
            VALUES (?,?,?)
            """,(id,user,0xFF))
    return (id,stamped)

def remove_repository(user : str, id : str):
    with DBA.open(GDB_PATH) as cur:
        cur.execute("DELETE FROM repositories WHERE id=?",(id,))
        cur.execute("DELETE FROM permissions WHERE repository=?",(id,))
    cache.delete_memoized(get_repository_id,id)
    cache.delete_memoized(get_repository_name,id)
    # TODO:update members.space

REPO_ALTER_FIELDS = {
    "alias": str,
    "name": str,
    "size": int
}
def update_repositry(user : str, id : str, data : dict):
    fields = [v for v in data.keys() if v in REPO_ALTER_FIELDS.keys()]
    fields = [v for v in fields if isinstance(data[v],REPO_ALTER_FIELDS[v]) ]
    values = [data[k] for k in fields]
    values += [id]
    with DBA.open(GDB_PATH) as cur:
        sql = ("UPDATE repositories SET "
            + (",".join(["%s=?" % (f,) for f in fields]))
             + " WHERE id=?")
        print(sql)
        cur.execute(sql,tuple(values))
    # delete cached name manually
    if "name" in data:
        cache.delete_memoized(get_repository_name,id)
    return {
        "id": id,
        "data": { k: data[k] for k in fields }
    }

def list_repositories(user : str):
    list = []
    keys = [ "id", "alias", "title", "owner", "size", "since", "updated", "permission" ]
    with DBA.open(GDB_PATH) as cur:
        cur.execute("""
            SELECT r.id, r.alias, r.name,
                r.owner_name, r.size,
                r.since, r.updated,
                p.permission
            FROM permissions AS p
            INNER JOIN repositories AS r ON r.id=p.repository
            WHERE p.member=? AND r.view_rank < p.permission
            ORDER BY r.updated DESC
            """,(user,))
        for row in cur.fetchall():
            list.append({ k: row[i] for i,k in enumerate(keys) })
    return list

def grant_permission(user : str, repo_id : str, member : str, rank : int):
    with DBA.open(GDB_PATH) as cur:
        cur.execute("""
            INSERT INTO permissions (repository,member,supervisor,permission)
            VALUES (?,?,?,?)
            """,(repo_id,member,user,rank))

def is_permission(user : str, id : str, rank : int):
    with DBA.open(GDB_PATH) as cur:
        cur.execute("""
            SELECT permission FROM permissions WHERE repository=? AND member=?
            """,(id,user))
        row = cur.fetchone()
        if row is None:
            return False
        accessiblity = rank & row[0]
        print(accessiblity)
    return accessiblity == rank
        