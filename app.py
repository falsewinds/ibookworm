from flask import Flask, request, render_template, redirect, jsonify
import localdb as iDB

app = Flask(__name__)

'''
Default Settings
'''

CAPTION = "I, Bookworm"
css = [ "normal.css" ]
jss = [ "reader.js" ]

def capt(suffix = None):
    if suffix is None:
        return CAPTION
    return CAPTION + ": " + suffix

'''
Views
'''

@app.route("/")
def loginpage():
    return render_template("landing.html.j2",
        title=CAPTION, css=css, js=jss, header=True)

@app.route("/me/")
def member():
    return render_template("default.html.j2",
        title=capt(), css=css)

@app.route("/view/<repo>/<doc>")
@app.route("/view/<repo>")
@app.route("/v/<repo>/<doc>")
@app.route("/v/<repo>")
def view(repo, doc = None):
    if doc is None:
        return render_template("default.html.j2",
            title=capt(repo), css=css)
    return render_template("default.html.j2",
        title=capt(doc), css=css)

@app.route("/edit/<repo>/<doc>")
@app.route("/edit/")
def edit(repo = None, doc = None):
    return render_template("editor.html.j2",
        title=capt("Editor"), css=css)

@app.route("/logout")
def logout():
    return render_template("default.html.j2",
        title=capt(), css=css)


'''
Controls
'''

@app.route("/create", methods=["POST"])
def create_repository():
    return jsonify({})
    #return redirect("view", repo="")

@app.route("/modify", methods=["POST"])
def modify_repository():
    return jsonify({})

@app.route("/open", methods=["POST"])
def new_document():
    repo = request.args.get("repository")
    doc_id = iDB.create_doc(repo+".db")
    return jsonify({ "doc_id": doc_id })

@app.route("/load", methods=["POST"])
def load_document():
    return jsonify({})

@app.route("/save", methods=["POST"])
def save_document():
    return jsonify({})

@app.route("/import/<repo>", methods=["POST"])
def import_documents(repo):
    return jsonify({})

@app.route("/peek/<job>", methods=["POST","GET"])
def peek_job_progress(job):
    return jsonify({})

@app.route("/download/<repo>")
def download(repo):
    return jsonify({})


'''
Error Handler : 404
'''
@app.errorhandler(404)
def page_not_found(err):
    return render_template("404.html.j2",
        title=capt("Page Not Found"),
        css=css, header=True), 404

if __name__ == "__main__":
    app.run()