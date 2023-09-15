from datetime import timedelta
from flask import Flask, request, session, render_template, redirect, jsonify
import globaldb as gDB
import localdb as iDB
import os

app = Flask(__name__)
#app.config["SECRET_KEY"] = os.urandom(24)
app.config["SECRET_KEY"] = b'\x17\x1c\xc6\xb5\xa9\xd2Er;\xd2\x0e\xf3I\xec\x06\xf0a\x1c04\xa8\x1b\xcf\xf6'
app.config["PERMANET_SESSION_LIFETIME"] = timedelta(days=31)
#gDB.initialize()

'''
Default Settings
'''

CAPTION = "I, Bookworm"
css = [ "normal.css", "form.css", "animation.css" ]
view_mods = [ "reader.js" ]
edit_mods = []

def capt(suffix = None):
    if suffix is None:
        return CAPTION
    return CAPTION + ": " + suffix

def check_membership():
    user = session.get("username")
    if user is None:
        return False
    token = session.get("accesstoken")
    if gDB.is_token_expired(token):
        if token is None:
            return False
        new_token = gDB.auto_log_in(user,token)
        if new_token is None:
            session["username"] = None
            session["accesstoken"] = None
            return False
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
    result, msg = gDB.log_in(user,request.values["password"])
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
    token = session["accesstoken"]
    gDB.set_token_expired(token)
    session["accesstoken"] = None
    session["message"] = None
    return redirect("/")

@app.route("/me/")
def member():
    if not check_membership():
        return redirect("/")
    return render_template("member.html.j2",
        title=capt(),
        css=css+["member.css"])

@app.route("/view/<repo>/<doc>")
@app.route("/view/<repo>")
@app.route("/v/<repo>/<doc>")
@app.route("/v/<repo>")
def view(repo, doc = None):
    if not check_membership():
        return redirect("/")
    if doc is None:
        return render_template("repository.html.j2",
            title=capt(), css=css, repo_id=repo)
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
    "error": 403,
    "message": "Invalid membership, please log-in again."
}

@app.route("/list", methods=["POST"])
def load_list():
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    return jsonify({})

@app.route("/create", methods=["POST"])
def create_repository():
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    title = request.values["title"]
    repo_id, stamped = gDB.add_repository(title)
    iDB.create_repository(repo_id)
    return jsonify({
        "repository": repo_id,
        "stamped_name": stamped
    })

@app.route("/modify", methods=["POST"])
def modify_repository():
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    return jsonify({})

@app.route("/open", methods=["POST"])
def new_document():
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    repo = request.args.get("repository")
    doc_id = iDB.create_doc(repo+".db")
    return jsonify({ "doc_id": doc_id })

@app.route("/load", methods=["POST"])
def load_document():
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    return jsonify({})

@app.route("/save", methods=["POST"])
def save_document():
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    return jsonify({})

@app.route("/import/<repo>", methods=["POST"])
def import_documents(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    return jsonify({})

@app.route("/peek/<job>", methods=["POST","GET"])
def peek_job_progress(job):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
    return jsonify({})

@app.route("/download/<repo>")
def download(repo):
    if not check_membership():
        return jsonify(ACCESS_DENIED)
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