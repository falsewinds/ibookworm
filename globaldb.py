import boto3
import hashlib
from localdb import DBA, DB_DIR
import os
from time import time

GDB_PATH = os.path.join(DB_DIR,"global.db")

def initialize():
    if os.path.exists(GDB_PATH):
        return
    with DBA.open(GDB_PATH) as cur:
        cur.execute("""
CREATE TABLE repositories (
    id      VARCHAR(32) NOT NULL PRIMARY_KEY,
    alias   VARCHAR(16),
    name    TEXT NOT NULL,
    size    INTEGER NOT NULL DEFAULT 0,
    owner   INTEGER NOT NULL,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
UNIQUE (owner,alias),
FOREIGN KEY (owner) REFERENCES members(id)
); """)
        cur.execute("""
CREATE TABLE members (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    username    VARCHAR(32) NOT NULL UNIQUE,
    
    size    INTEGER NOT NULL DEFAULT 0,
    owner   INTEGER NOT NULL,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
UNIQUE (owner,alias),
FOREIGN KEY (owner) REFERENCES member(id)
); """
        )

def is_token_expired(token : str):
    if token is None:
        return True
    return False

# return new, non-expired token
def auto_log_in(user : str, token : str):
    return None

def log_in(user : str, pwd : str):
    # TODO: log-in using user & pwd
    return (True,"the-fake-given-access-token")
    #return (False,"Invalid Access")


# TODO: remove token from GlobalDB/DynamoDB
def set_token_expired(token : str):
    pass


def add_repository(title : str):
    stamped_title = title + "." + str(int(time()))
    repo_id = hashlib.md5(stamped_title).hexdigest()
    with DBA.open(GDB_PATH) as cur:
        cur.execute("""
            INSERT INTO repositorires (id,name)
            VALUES (?,?,)
            """,(repo_id,title,))
    return (repo_id,stamped_title)