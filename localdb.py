from globaldb import Repository
import json
import sqlite3

CREATE_TABLE_toc = '''
CREATE TABLE toc (
    id		INT NOT NULL PRIMARY KEY AUTOINCREMENT,
    parent	INT DEFAULT NULL,
    after	INT DEFAULT NULL,
    doc_id	INT DEFAULT NULL,
    title	TEXT NOT NULL DEFAULT '',
    editor	TEXT NOT NULL,
    updated	TEXT NOT NULL,
  FOREIGN KEY (parent) REFERENCES toc(id),
  FOREIGN KEY (after) REFERENCES toc(id),
  FOREIGN KEY (doc_id) REFERENCES doc(id)
);'''

CREATE_TABLE_doc = '''
CREATE TABLE doc (
    id		INT NOT NULL PRIMARY KEY AUTOINCREMENT,
    title	TEXT NOT NULL DEFAULT 'unnamed',
    type	TEXT NOT NULL DEFAULT 'article',
    version	INT NOT NULL DEFAULT 0,
    metadata	TEXT NOT NULL DEFAULT '{}',
    content	TEXT NOT NULL DEFAULT '{}',
    created	TEXT NOT NULL,
    updated	TEXT NOT NULL
);'''

'''
doc.type:
 - article : simple richtext { "richtext": true/false, "lines": [ STRING ] }
 - translation : simple text { "language": STRING, "lines": [ STRING ] }
 - map : { "width": INT, "height": INT, "center": POINT, "regions": { ... } }
 - glossary : like article, but serve for keyword purpose.
 - chronicle : { "calendar": { "format": (calendar format string) }, "events": [ EVENT ] }
 - relation : { "character": [ STRING ], "relations": [ RELATION ] }
'''

CREATE_TABLE_ver = '''
CREATE TABLE ver (
    doc_id	INT DEFAULT NULL,
    version	INT NOT NULL DEFAULT 0,
    changes	TEXT NOT NULL DEFAULT '{}',
    editor_id	INT NOT NULL,
    saved	TEXT NOT NULL,
  FOREIGN KEY (doc_id) REFERENCES doc(id),
  PRIMARY KEY (doc_id, version)
);'''

CREATE_TABLE_inf = '''
CREATE TABLE inf (
    id		INT NOT NULL PRIMARY KEY AUTOINCREMENT,
    inf_key	TEXT NOT NULL,
    inf_val	TEXT NOT NULL
);'''
