import io
import json
import mimetypes
import os

import requests
from flask import Flask, request, redirect, send_file, session, url_for
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

app = Flask(__name__)
app.config.from_prefixed_env()  # loads FLASK_SECRET_KEY

client_id = os.environ["PRIVATE_GHP_CLIENT_ID"]
client_secret = os.environ["PRIVATE_GHP_CLIENT_SECRET"]
authorization_base_url = "https://github.com/login/oauth/authorize?scope=repo"
token_url = "https://github.com/login/oauth/access_token"
head = """
<head>
  <title>private-ghp</title>
  <style>
    body {
      background-color: black;
    }
    input {
      background-color: black;
      border-color: white;
      border-style: solid;
      border-width: 1px;
    }
    input#url {
      width: 70%;
    }
    a, h1, input, label, p, pre {
      font-family: monospace;
      color: white;
    }
    a {
      text-decoration: none;
    }
    a:hover {
      color: blue;
    }
  </style>
</head>
"""


def ensure_auth():
    github = None
    redirect_response = None
    logged_in = False
    if "oauth_token" in session:
        github = OAuth2Session(client_id, token=session["oauth_token"])
        logged_in = True
    else:
        github = OAuth2Session(client_id)
        authorization_url, state = github.authorization_url(authorization_base_url)
        session["oauth_state"] = state
        redirect_response = redirect(authorization_url)
    return github, redirect_response, logged_in


@app.route("/")
def root():
    github, redirect_response, logged_in = ensure_auth()
    user = github.get("https://api.github.com/user").json() if logged_in else None
    return (
        head
        + "<h1>private-ghp</h1>"
        + (
            (
                f"<p>logged in as {user.get('login', 'unknown user')}</p>"
                f"<a href='{url_for('logout')}'>logout</a><br><br>"
                "<form action='/go' method='post'>"
                "<label for='url'>paste github url:</label>"
                "<input type='text' id='url' name='url'>"
                "<input type='submit' value='go'><br><br>"
                "</form>"
            )
            if logged_in
            else f"<a href='{url_for('login')}'>login</a>"
        )
    )


@app.route("/login", methods=["GET"])
def login():
    github, redirect_response, logged_in = ensure_auth()
    if redirect_response:
        return redirect_response
    return redirect(url_for("root"))


@app.route("/callback", methods=["GET"])
def callback():
    if "oauth_state" not in session:
        return redirect(url_for("root"))
    github = OAuth2Session(client_id, state=session["oauth_state"])
    token = github.fetch_token(
        token_url, client_secret=client_secret, authorization_response=request.url
    )
    session["oauth_token"] = token
    return redirect(url_for("root"))


@app.route("/logout", methods=["GET"])
def logout():
    github, redirect_response, logged_in = ensure_auth()
    if not logged_in:
        return redirect(url_for("root"))
    response = requests.delete(
        f"https://api.github.com/applications/{client_id}/grant",
        data=json.dumps({"access_token": session["oauth_token"]["access_token"]}),
        auth=HTTPBasicAuth(client_id, client_secret),
    )
    session.clear()
    if response.status_code == 204:
        return redirect(url_for("root"))
    return (
        head + f"<pre>{response.json()}</pre>"
        f"<a href='{url_for('root')}'>return home</a>"
    )


@app.route("/go", methods=["POST"])
def go():
    return redirect("/" + request.form["url"])


@app.route(
    "/https://github.com/<owner>/<repo>/blob/<rev>/<path:file_path>",
    methods=["GET"],
)
@app.route(
    "/https://github.com/<owner>/<repo>/blob/<rev>/",
    methods=["GET"],
    defaults={"file_path": None},
)
def content(owner, repo, rev, file_path):
    # ensure auth
    github, redirect_response, logged_in = ensure_auth()
    if redirect_response:
        return redirect_response

    # rewrite URLs ending in / to /index.html
    if file_path is None:
        file_path = "index.html"
    elif file_path.endswith("/"):
        file_path += "index.html"

    # deduce mimetype
    mimetype, _ = mimetypes.guess_type(file_path)
    if file_path.endswith(".md"):
        mimetype = "text/plain"
    elif file_path.endswith(".map"):
        mimetype = "application/json"
    elif file_path.endswith(".woff"):
        mimetype = "font/woff"
    if mimetype is None:
        raise ValueError(f"could not deduce mimetype for {file_path}")

    # get content
    content = github.get(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={rev}",
        headers={"Accept": "application/vnd.github.raw"},
    )

    # return response
    return send_file(io.BytesIO(content.content), mimetype=mimetype)


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    app.secret_key = os.urandom(24)
    app.run(debug=True)
