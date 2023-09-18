from appconfig import configure_app, cache, db_cfg, TIMEOUT_DAY
from flask import Flask, request, session, abort, render_template, redirect, jsonify
import globaldb as gDB
import localdb as iDB

app = Flask(__name__)
configure_app(app)
# GlobalDB Configuration
gDB.initialize(db_cfg)

'''
Default Settings
'''

CAPTION = "I, Bookworm"

def capt(suffix = None):
    if suffix is None:
        return CAPTION
    return CAPTION + ": " + suffix

css = [ "normal.css", "form.css", "animation.css" ]
view_mods = [ "reader.js" ]
edit_mods = []

def check_membership():
    user = session.get("username")
    if user is None:
        return False
    token = session.get("accesstoken")
    if token is None:
        return False
    expired, new_token = gDB.is_token_expired(user,token)
    if expired:
        if new_token is None:
            session["username"] = None
            session["accesstoken"] = None
            return False
        session["accesstoken"] = new_token
    return True


'''
Views
'''

@app.route("/")
def landing():
    if check_membership():
        return redirect("/me/")
    return render_template("landing.html.j2",
        title=capt(), header=True,
        css=css,
        username=session.get("username"),
        errmsg=session.get("message"))

@app.route("/login", methods=["POST"])
def login():
    user = request.values["username"]
    result, msg = gDB.get_token(user,request.values["password"])
    if result:
        session["username"] = user
        session["accesstoken"] = msg
        session.permanent = True
        return redirect("/me/")
    else:
        session["message"] = msg
        return redirect("/")

@app.route("/logout")
def logout():
    user = session.get("username")
    token = session["accesstoken"]
    gDB.set_token_expired(user,token)
    session["accesstoken"] = None
    session["message"] = None
    return redirect("/")

@app.route("/me/")
def member():
    if not check_membership():
        return redirect("/")
    user = session.get("username")
    name = gDB.get_member_name(user)
    if name is None:
        name = user
    return render_template("member.html.j2",
        title=capt(), css=css+["member.css"],
        name=name)

@app.route("/view/<repo>/")
@app.route("/view/<repo>")
@app.route("/v/<repo>/")
@app.route("/v/<repo>")
def view_toc(repo):
    if not check_membership():
        return redirect("/")
    id = gDB.get_repository_id(repo)
    name = gDB.get_repository_name(id)
    if name is None:
        abort(404)
    return render_template("repository.html.j2",
        title=name, css=css+["repository.css"],
        repo_id=id, repo_name=name)

@app.route("/view/<repo>/<doc>")
@app.route("/v/<repo>/<doc>")
def view_doc(repo, doc):
    if not check_membership():
        return redirect("/")
    return render_template("viewer.html.j2",
        title=capt("Viewer"),
        css=css, js=view_mods,
        doc_id=doc)

@app.route("/edit/<repo>/<doc>")
@app.route("/edit/")
def edit(repo = None, doc = None):
    if not check_membership():
        return redirect("/")
    return render_template("editor.html.j2",
        title=capt("Editor"), css=css, js=edit_mods)


'''
Controls
'''

ACCESS_DENIED = {
    "error": 401,
    "message": "Invalid membership, please log-in again."
}

def try_get_value(key, def_val):
    if request.is_json:
        jsondata = request.get_json()
        if key in jsondata:
            return jsondata[key]
        return def_val
    val = request.values.get(key)
    if val is None:
        return def_val
    return val

def try_get_dict():
    if request.is_json:
        return request.get_json()
    return request.values.to_dict()

@app.route("/list", methods=["POST"])
@cache.cached(timeout=TIMEOUT_DAY)
def load_list():
    print(request.path)
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    repo_list = gDB.list_repositories(user)
    return jsonify(repo_list)


@app.route("/list/<repo>", methods=["POST"])
@cache.cached(timeout=TIMEOUT_DAY)
def load_document_list(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    if not gDB.is_permission(user,repo,0x01):
        return jsonify({
            "error": 403,
            "message": "No permission."
        })
    path = iDB.get_db_path(user,repo)
    return jsonify(iDB.list_repository(path))


@app.route("/create", methods=["POST"])
def create_repository():
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    title = try_get_value("title",None)
    if title is None:
        return jsonify({
            "error": 406,
            "message": "Must have a title."
        })
    cache.delete("view/%s" % "/list")
    repo, stamped = gDB.create_repository(user,title)
    path = iDB.get_db_path(user,repo)
    iDB.create_repository(path)
    return jsonify({
        "repository": repo
    })

@app.route("/modify/<repo>", methods=["POST"])
def modify_repository(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    if not gDB.is_permission(user,repo,0xFF):
        return jsonify({
            "error": 403,
            "message": "No permission."
        })
    cache.delete("view/%s" % "/list")
    return jsonify(gDB.update_repositry(user,repo,try_get_dict()))

@app.route("/remove/<repo>", methods=["POST"])
def remove_repository(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    if not gDB.is_permission(user,repo,0xFF):
        return jsonify({
            "error": 403,
            "message": "No permission."
        })
    cache.delete("view/%s" % "/list")
    name = gDB.get_repository_name(repo)
    gDB.remove_repository(user,repo)
    return jsonify({
        "id": repo,
        "name": name
    })


@app.route("/open/<repo>", methods=["POST"])
def new_document(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    # TODO: check rank
    if not gDB.is_permission(user,repo,0xFF):
        return jsonify({
            "error": 403,
            "message": "No permission."
        })
    cache.delete("view/%s" % "/list")
    cache.delete("view/%s" % f"/list/{repo}")
    path = iDB.get_db_path(user,repo)
    doc_id = iDB.create_doc(path)
    return jsonify({ "doc_id": doc_id })

@app.route("/load/<repo>/<doc_id>", methods=["POST"])
@cache.cached(timeout=TIMEOUT_DAY)
def load_document(repo,doc_id):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    path = iDB.get_db_path(user,repo)
    return jsonify({})

@app.route("/save/<repo>/<doc_id>", methods=["POST"])
def save_document(repo,doc_id):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    cache.delete("view/%s" % f"/load/{repo}/{doc_id}")
    user = session.get("username")
    return jsonify({})

@app.route("/import/<repo>", methods=["POST"])
def import_documents(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    #cache.delete("view/%s" % "/list")
    cache.delete("view/%s" % f"/list/{repo}")
    user = session.get("username")
    return jsonify({})

@app.route("/peek/<job>", methods=["POST","GET"])
def peek_job_progress(job):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    #user = session.get("username")
    return jsonify({})

@app.route("/download/<repo>")
def download(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    #user = session.get("username")
    return jsonify({})


'''
Error Handler : 404
'''
@app.errorhandler(404)
def page_not_found(err):
    return render_template("404.html.j2",
        title=capt("Page Not Found"),
        header=True, noapp=True,
        css=["normal.css"],
        errmsg=err), 404

if __name__ == "__main__":
    app.run()
    #app.run(host="0.0.0.0", port=5000)