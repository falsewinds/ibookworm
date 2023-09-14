import boto3
from flask import session
from localdb import DBA, DB_DIR
import os

def check_membership():
    user = session.get("username")
    if user is None:
        return False
    token = session.get("accesstoken")
    if is_token_expired(token):
        if token is None:
            return False
        new_token = auto_log_in(user,token)
        if new_token is None:
            session["username"] = None
            session["accesstoken"] = None
            return False
    return True

def get_username():
    return session.get("username")

def login(user : str, pwd : str):
    # TODO: log-in using user & pwd
    # if success
    session["username"] = user
    session["accesstoken"] = "the-fake-given-access-token"
    session.permanent = True

def logout():
    token = session["accesstoken"]
    session["accesstoken"] = None
    set_token_expired(token)



'''
Real DB function(s)
'''

def initialize():
    gdb_path = os.path.join(DB_DIR,"global.db")
    if os.path.exists(gdb_path):
        return
    with DBA.open(gdb_path) as cur:
        cur.execute("""
CREATE TABLE repositories (
    id      VARCHAR(32) PRIMARY_KEY,
    name    TEXT NOT NULL,
);
        """)

def is_token_expired(token : str):
    if token is None:
        return True
    return False

# return new, non-expired token
def auto_log_in(user : str, token : str):
    return None

# TODO: remove token from GlobalDB/DynamoDB
def set_token_expired(token : str):
    pass