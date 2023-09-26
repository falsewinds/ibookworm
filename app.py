from appconfig import configure_app
from flask import Flask, request, session, render_template, redirect, jsonify
import globaldb as gDB
import localdb as iDB
#from sqlite_lib import get_db_path

app = Flask(__name__)
configure_app(app)

'''-------------------------------------------------------------
Default Settings
 - initialize(cfg)
-------------------------------------------------------------'''

CAPTION = "I, Bookworm"
def capt(suffix = None):
    if suffix is None:
        return CAPTION
    return CAPTION + ": " + suffix

css = [ "normal.css", "form.css", "animation.css" ]
app_js = [ "dom_wrapper.js", "dom_layout.js", "ibookworm.js", "memberbar.js" ]
view_mods = [ "reader.js" ]
edit_mods = [ "puretexteditor.js" ]

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


'''-------------------------------------------------------------
Views
 - /
 - /login
 - /logout
 - /me/
 - /view/<repo>/
 - /view/<repo>/<doc>
 - /edit/<repo>/<doc>
 - /worker.js
-------------------------------------------------------------'''

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
        title=capt(),
        js=["memberbar.js"],
        css=css+["member.css"],
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
        from flask import abort
        abort(404)
    return render_template("repository.html.j2",
        title=name,
        js=["memberbar.js"],
        css=css+["repository.css"],
        repo_name=name)

@app.route("/view/<repo>/<doc>")
@app.route("/v/<repo>/<doc>")
def view_doc(repo, doc):
    if not check_membership():
        return redirect("/")
    return render_template("viewer.html.j2",
        title=capt("Viewer"),
        js=["memberbar.js"]+view_mods,
        css=css+["viewer.css"],
        doc_id=doc)

@app.route("/edit/<repo>/<doc>")
@app.route("/edit/<repo>/")
@app.route("/edit/")
def edit(repo = None, doc = None):
    if not check_membership():
        return redirect("/")
    return render_template("editor.html.j2",
        title=capt("Editor"),
        js=["memberbar.js"]+edit_mods,
        css=css+["editor.css"])

@app.route("/worker.js")
def service_worker_js():
    from flask import make_response
    response = make_response(
        render_template("worker.js.j2",
            css=css, js=app_js+view_mods+edit_mods
        ))
    response.headers["Content-Type"] = "application/javascript"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


'''-------------------------------------------------------------
Controls
-------------------------------------------------------------'''

ACCESS_DENIED = {
    "error": 401,
    "message": "Invalid membership, please log-in again."
}

def try_get_value(key, def_val):
    if request.is_json:
        jsondata = request.get_json()
        print(jsondata)
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

'''-------------------------------------------------------------
Controls : repository
 - /list
 - /list/<repo>
 - /create
 - /modify/<repo>
 - /remove/<repo>
-------------------------------------------------------------'''

@app.route("/list", methods=["POST"])
def load_list():
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    repo_list = gDB.list_repositories(user)
    return jsonify(repo_list)


@app.route("/list/<repo>", methods=["POST"])
def load_document_list(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    id = gDB.get_repository_id(repo)
    if not gDB.is_permission(user,id,0x01):
        return jsonify({
            "error": 403,
            "message": "No permission."
        })
    return jsonify(iDB.list_toc(user,id))


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
    repo, stamped = gDB.create_repository(user,title)
    iDB.create_repository(user,repo)
    return jsonify({
        "repository": repo
    })

@app.route("/modify/<repo>", methods=["POST"])
def modify_repository(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    id = gDB.get_repository_id(repo)
    if not gDB.is_permission(user,id,0xFF):
        return jsonify({
            "error": 403,
            "message": "No permission."
        })
    return jsonify(gDB.update_repositry(user,id,try_get_dict()))

@app.route("/remove/<repo>", methods=["POST"])
def remove_repository(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    id = gDB.get_repository_id(repo)
    if not gDB.is_permission(user,id,0xFF):
        return jsonify({
            "error": 403,
            "message": "No permission."
        })
    name = gDB.get_repository_name(id)
    gDB.remove_repository(user,id)
    return jsonify({
        "id": repo,
        "name": name
    })

'''-------------------------------------------------------------
Controls : document
 - /load/<repo>/<doc>
 - /save/<repo>/<doc>
 - /save/<repo>/
 - /save/<repo>
 - /import/<repo>
 - /peek/<job>
 - /download/<repo>
-------------------------------------------------------------'''

@app.route("/load/<repo>/<doc_id>", methods=["POST"])
def load_document(repo,doc_id):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    return jsonify(iDB.read_doc(user,repo,doc_id))

@app.route("/save/<repo>/<doc_id>", methods=["POST"])
@app.route("/save/<repo>/", methods=["POST"])
@app.route("/save/<repo>", methods=["POST"])
def save_document(repo,doc_id = None):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    if doc_id is None:
        doc_id = iDB.create_doc(user,repo,
            try_get_value("title","unnamed"),
            try_get_value("type","article"),
            {},
            try_get_value("content",""))
        ver = 0
    else:
        doc_id, ver = iDB.update_doc(user,repo,doc_id,try_get_dict())
    return jsonify({
        "doc_id": doc_id,
        "version": ver
    })

@app.route("/import/<repo>", methods=["POST"])
def import_documents(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    user = session.get("username")
    return jsonify({})

@app.route("/download/<repo>")
def download(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    #user = session.get("username")
    return jsonify({})

'''-------------------------------------------------------------
Controls : async job
 - /peek/<job>
-------------------------------------------------------------'''

@app.route("/peek/<job>", methods=["POST","GET"])
def peek_job_progress(job):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    #user = session.get("username")
    return jsonify({})


'''-------------------------------------------------------------
Error Handler : 404
-------------------------------------------------------------'''

@app.errorhandler(404)
def page_not_found(err):
    return render_template("404.html.j2",
        title=capt("Page Not Found"),
        header=True, noapp=True,
        css=["normal.css"],
        errmsg=err), 404


'''-------------------------------------------------------------
Activate FalskApp
-------------------------------------------------------------'''
if __name__ == "__main__":
    app.run()
    #app.run(host="0.0.0.0", port=5000)