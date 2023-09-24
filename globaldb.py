from appconfig import cache, db_cfg, TIMEOUT_DAY, EXPIRED_TIME
import boto3
import hashlib
import json
from time import time
from sqlite_lib import DBA, TRIGGER_FORMAT, INDEX_FORMAT, local_now_to_utc, is_past


'''-------------------------------------------------------------
Global Database
 - initialize(cfg)
-------------------------------------------------------------'''
CREATE_TABLE_repositories = """
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
);"""

CREATE_TABLE_members = """
CREATE TABLE members (
    id          VARCHAR(32) NOT NULL PRIMARY KEY,
    email       TEXT NOT NULL UNIQUE,
    name        TEXT,
    layout      TEXT NOT NULL DEFAULT '{}',
    bookmarks   TEXT NOT NULL DEFAULT '{}',
    space       INTEGER NOT NULL DEFAULT 0,
    since       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

CREATE_TABLE_permissions = """
CREATE TABLE permissions (
    repository  VARCHAR(32) NOT NULL,
    member      VARCHAR(32) NOT NULL,
    supervisor  VARCHAR(32),
    permission  INTEGER NOT NULL DEFAULT 1,
PRIMARY KEY (repository,member),
FOREIGN KEY (repository) REFERENCES repositories(id),
FOREIGN KEY (member) REFERENCES members(id),
FOREIGN KEY (supervisor) REFERENCES members(id)
);"""

CREATE_TABLE_tokens = """
CREATE TABLE tokens (
    token       VARCHAR(32) NOT NULL PRIMARY KEY,
    member      VARCHAR(32) NOT NULL,
    secret      VARCHAR(32) NOT NULL,
    expired_at  TIMESTAMP NOT NULL,
    ip_addr     TEXT,
    agent       TEXT,
FOREIGN KEY (member) REFERENCES members(id)
);"""

GDB_PATH = None
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
        cur.execute(CREATE_TABLE_repositories)
        cur.execute(TRIGGER_FORMAT.format(table="repositories",field="updated"))
        cur.execute(CREATE_TABLE_members)
        cur.execute(CREATE_TABLE_permissions)
        cur.execute(INDEX_FORMAT.format(table="permissions",field="repository"))
        cur.execute(INDEX_FORMAT.format(table="permissions",field="member"))
        cur.execute(CREATE_TABLE_tokens)
        cur.execute(INDEX_FORMAT.format(table="tokens",field="member"))

# GlobalDB Configuration
initialize(db_cfg)

'''-------------------------------------------------------------
Name Cache function(s)
 - get_member_name(user_id)
 - get_repository_id(repo_id | repo_alias)
 - get_repository_name(repo_id)
-------------------------------------------------------------'''

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


'''-------------------------------------------------------------
Member
 - get_token(user_id,password)
 - is_token_expired(user_id,token)
 - set_token_expired(user_id,token)
 + get_user_data(user_id)
-------------------------------------------------------------'''
FAKE_ONLY_TOKEN = "the-fake-given-access-token"
FAKE_SECRET = "the-fake-secret-for-test"

def save_token(user : str, secret : str):
    #expired = datetime.now() + EXPIRED_TIME
    #expired_at = expired.strftime(DATETIME_FORMAT)
    expired_at = local_now_to_utc(EXPIRED_TIME)
    token_str = "-".join([user,secret,expired_at])
    token = hashlib.md5(token_str.encode('utf-8')).hexdigest()
    name = get_member_name(user)
    with DBA.open(GDB_PATH) as cur:
        if name is None:
            name = user
            email = user + "@example.com"
            # TODO: get email,name from Cognito
            cur.execute("""
                INSERT INTO members (id,email,name)
                VALUES (?,?,?)
                """,(user,email,name))
            cache.delete_memoized(get_member_name,user)
            cache.delete_memoized(get_user_data,user)
        cur.execute("""
            INSERT INTO tokens (token,member,secret,expired_at)
            VALUES (?,?,?,?)
            """,(token,user,secret,expired_at))
        print((token,user,secret,expired_at))
    return token

def get_token(user : str, pwd : str):
    cognito_token = FAKE_SECRET
    # TODO: log-in using user & pwd
    if cognito_token is None:
        return (False,"Invalid Access")
    token = save_token(user,cognito_token)
    return (True,token)

@cache.memoize(timeout=TIMEOUT_DAY)
def is_token_expired(user : str, token : str):
    with DBA.open(GDB_PATH) as cur:
        cur.execute("""
            SELECT secret, expired_at FROM tokens WHERE token=? AND member=?
            """,(token,user))
        row = cur.fetchone()
        if row is None:
            return (True,None)
        if is_past(row[1]):
            cur.execute("DELETE FROM tokens WHERE token=?",(token,))
            cache.delete_memoized(is_token_expired,user,token)
            cognito_token = None
            # TODO: try re-new token using secret(row[0])
            if cognito_token is None:
                return (True,None)
            token = save_token(user,cognito_token)
            return (True,token)
    return (False,None)

def set_token_expired(user : str, token : str):
    # TODO: remove token from GlobalDB/Cognito
    with DBA.open(GDB_PATH) as cur:
        cur.execute(
            "DELETE FROM tokens WHERE token=? AND member=?",
            (token,user))
    cache.delete_memoized(is_token_expired,user,token)

@cache.memoize(timeout=TIMEOUT_DAY)
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


'''-------------------------------------------------------------
Repository
 - create_repository(user_id,title)
 - remove_repository(user_id,repo_id)
 - update_repositry(user_id,repo_id,data)
 + list_repositories(user_id)
 - grant_permission(user_id,member,repo_id,rank)
 + get_permission(user_id,repo_id)
 - is_permission(user_id,repo_id,rank)
-------------------------------------------------------------'''

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
    cache.delete_memoized(list_repositories,user)
    cache.delete_memoized(get_permission,user,id)
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
    cache.delete_memoized(list_repositories,user)
    # delete cached name manually
    if "name" in data:
        cache.delete_memoized(get_repository_name,id)
    return {
        "id": id,
        "data": { k: data[k] for k in fields }
    }

REPOSITORY_KEYS = [
     "id", "alias",
     "title", "owner", "size",
     "since", "updated",
     "permission"
]
@cache.memoize(timeout=TIMEOUT_DAY)
def list_repositories(user : str):
    list = []
    with DBA.open(GDB_PATH) as cur:
        cur.execute("""
            SELECT r.id, r.alias, r.name,
                r.owner_name, r.size,
                r.since, r.updated,
                p.permission
            FROM repositories AS r
            LEFT JOIN permissions AS p ON p.repository=r.id
            WHERE r.view_rank=0 OR (p.member=? AND r.view_rank < p.permission)
            ORDER BY r.updated DESC
            """,(user,))
        for row in cur.fetchall():
            list.append({ k: row[i] for i,k in enumerate(REPOSITORY_KEYS) })
    return list

def grant_permission(user : str, repo_id : str, member : str, rank : int):
    with DBA.open(GDB_PATH) as cur:
        cur.execute("""
            INSERT INTO permissions (repository,member,supervisor,permission)
            VALUES (?,?,?,?)
            """,(repo_id,member,user,rank))
    cache.delete_memoized(get_permission,member,repo_id)

@cache.memoize(timeout=TIMEOUT_DAY)
def get_permission(user : str, id : str):
    with DBA.open(GDB_PATH) as cur:
        cur.execute("""
            SELECT permission FROM permissions WHERE repository=? AND member=?
            """,(id,user))
        row = cur.fetchone()
        if row is None:
            return 0
        return row[0]

def is_permission(user : str, id : str, rank : int):
    user_rank = get_permission(user,id)
    accessiblity = user_rank & rank
    print(accessiblity)
    return accessiblity == rank
