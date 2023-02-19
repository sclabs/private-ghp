import base64
import json
import mimetypes
import os

import requests
from flask import Flask, Response, request, redirect, session, url_for
from flask.json import jsonify
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
    a, h1, p {
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
                f"<p>logged in as {user['login']}</p>"
                f"<a href='{url_for('logout')}'>logout</a>"
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
    if response.status_code == 204:
        del session["oauth_state"]
        del session["oauth_token"]
        return redirect(url_for("root"))
    return (
        head + f"<pre>{response.json()}</pre>"
        f"<a href='{url_for('root')}'>return home</a>"
    )


@app.route("/<owner>/<repo>/<rev>/<file_path>", methods=["GET"])
def profile(owner, repo, rev, file_path):
    github, redirect_response, logged_in = ensure_auth()
    if redirect_response:
        return redirect_response
    content_dict = github.get(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={rev}"
    ).json()
    content = base64.b64decode(content_dict["content"])
    mimetype, _ = mimetypes.guess_type(file_path)
    if file_path.endswith(".md"):
        mimetype = "text/plain"
    return Response(content, mimetype=mimetype)


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    app.secret_key = os.urandom(24)
    app.run(debug=True)
