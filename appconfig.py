from datetime import timedelta
from flask import Flask
from flask_caching import Cache
import os
from redis import Redis
import yaml

with open("data/config.yaml","r") as f:
    cfg = yaml.safe_load(f)

# Caching
cache_cfg = {
    "CACHE_TYPE": "simple",
    "CACHE_KEY_PREFIX": "ibookworm"
}
if "Redis" in cfg:
    redis_host = "localhost"
    redis_port = 6379
    if "host" in cfg["Redis"]:
        redis_host = cfg["Redis"]["host"]
    if "post" in cfg["Redis"]:
        redis_port = int(cfg["Redis"]["port"])
    redis = Redis()
    cache_cfg["CACHE_TYPE"] = "redis"
    cache_cfg["CACHE_REDIS_URL"] = f"redis://{redis_host}:{redis_port}"

TIMEOUT_DAY = 24 * 60 * 60

if "expire" in cfg:
    expire_day = int(cfg["expire"])
    EXPIRED_TIME = timedelta(days=expire_day)
else:
    EXPIRED_TIME = timedelta(days=60)

cache = Cache(config=cache_cfg)

db_cfg = cfg["simpleDB"]

def configure_app(app : Flask):
    # Web Application Configuration
    flask_cfg = cfg["flask"]
    if "secrect" in flask_cfg:
        app.config["SECRET_KEY"] = flask_cfg["secrect"]
    else:
        secrect = os.urandom(24)
        app.config["SECRET_KEY"] = secrect
        print(secrect)
    app.config["PERMANET_SESSION_LIFETIME"] = EXPIRED_TIME
    # Caching
    cache.init_app(app)
    cache.clear()