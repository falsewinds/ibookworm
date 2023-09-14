from datetime import timedelta
from flask import Flask, request, render_template, redirect, jsonify
import globaldb as gDB
import localdb as iDB
import os

app = Flask(__name__)
#app.config["SECRET_KEY"] = os.urandom(24)
app.config["SECRET_KEY"] = b'\x17\x1c\xc6\xb5\xa9\xd2Er;\xd2\x0e\xf3I\xec\x06\xf0a\x1c04\xa8\x1b\xcf\xf6'
app.config["PERMANET_SESSION_LIFETIME"] = timedelta(days=31)

'''
Default Settings
'''

CAPTION = "I, Bookworm"
css = [ "normal.css", "form.css" ]
view_mods = [ "reader.js" ]
edit_mods = []

def capt(suffix = None):
    if suffix is None:
        return CAPTION
    return CAPTION + ": " + suffix

'''
Views
'''

@app.route("/")
def landing():
    if gDB.check_membership():
        return redirect("/me/")
    return render_template("landing.html.j2",
        title=capt(), css=css,
        header=True, username=gDB.get_username())

@app.route("/login", methods=["POST"])
def login():
    un = request.values["username"]
    pwd = request.values["username"]
    if gDB.login(un,pwd):
        return redirect("/me/")
    return redirect("/")

@app.route("/logout")
def logout():
    gDB.logout()
    return redirect("/")

@app.route("/me/")
def member():
    if not gDB.check_membership():
        return redirect("/")
    return render_template("member.html.j2",
        title=capt(), css=css)

@app.route("/view/<repo>/<doc>")
@app.route("/view/<repo>")
@app.route("/v/<repo>/<doc>")
@app.route("/v/<repo>")
def view(repo, doc = None):
    if not gDB.check_membership():
        return redirect("/")
    if doc is None:
        return render_template("repository.html.j2",
            title=capt(repo), css=css)
    return render_template("viewer.html.j2",
        title=capt(doc), css=css, js=view_mods)

@app.route("/edit/<repo>/<doc>")
@app.route("/edit/")
def edit(repo = None, doc = None):
    if not gDB.check_membership():
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

@app.route("/create", methods=["POST"])
def create_repository():
    if not gDB.check_membership():
        return jsonify(ACCESS_DENIED)
    repo = request.values["repository"]
    return jsonify({})

@app.route("/modify", methods=["POST"])
def modify_repository():
    if not gDB.check_membership():
        return jsonify(ACCESS_DENIED)
    return jsonify({})

@app.route("/open", methods=["POST"])
def new_document():
    if not gDB.check_membership():
        return jsonify(ACCESS_DENIED)
    repo = request.args.get("repository")
    doc_id = iDB.create_doc(repo+".db")
    return jsonify({ "doc_id": doc_id })

@app.route("/load", methods=["POST"])
def load_document():
    if not gDB.check_membership():
        return jsonify(ACCESS_DENIED)
    return jsonify({})

@app.route("/save", methods=["POST"])
def save_document():
    if not gDB.check_membership():
        return jsonify(ACCESS_DENIED)
    return jsonify({})

@app.route("/import/<repo>", methods=["POST"])
def import_documents(repo):
    if not gDB.check_membership():
        return jsonify(ACCESS_DENIED)
    return jsonify({})

@app.route("/peek/<job>", methods=["POST","GET"])
def peek_job_progress(job):
    if not gDB.check_membership():
        return jsonify(ACCESS_DENIED)
    return jsonify({})

@app.route("/download/<repo>")
def download(repo):
    if not gDB.check_membership():
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