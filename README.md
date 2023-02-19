private-ghp
===========

A Flask proxy to serve pages from private repos using OAuth2

Premise
-------

Pointing your browser to

    https://<my_domain>/<repo_owner>/<repo_name>/<ref>/<file_path>

will display the contents of that file in your browser (even if the repo is
private) using your GitHub permissions via OAuth2.

Motivation
----------

GitHub Pages provides a convenient way to host static HTML content related to a
repo (docs, reports, etc.) directly from GitHub. However, it is not possible to
control access to GitHub Pages that belong to private repos unless you have
GitHub Enterprise Cloud. As a workaround, we use OAuth2 to fetch content from a
specified branch of a specified GitHub repo using the user's own permissions.

This project was inspired by [john-dev/private-ghp](https://github.com/john-dev/private-ghp).

Local testing quickstart
------------------------

    git clone https://github.com/sclabs/private-ghp
    cd private-ghp
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    export PRIVATE_GHP_CLIENT_ID=...  # see below
    export PRIVATE_GHP_CLIENT_SECRET=...
    python app.py

Navigate to http://localhost:5000/ to complete the login flow.

Then navigate to e.g.

http://localhost:5000/sclabs/aotd-graph-d3/master/index.html

to see the file `index.html` from the `master` branch of the
[sclabs/aotd-graph-d3](https://github.com/sclabs/aotd-graph-d3) repo.

Creating the GitHub OAuth App
-----------------------------

[Create a new OAuth App](https://github.com/settings/applications/new), setting
the Authorization callback URL to `http://localhost:5000/callback` for local
testing, or `https://<your_domain>/callback` for a deployed instance of your
app.

Then generate a client ID and secret for that app and store them as
`PRIVATE_GHP_CLIENT_ID` and `PRIVATE_GHP_CLIENT_SECRET` env vars.

Docker image
------------

The docker image is based on [tiangolo/meinheld-gunicorn-flask](https://hub.docker.com/r/tiangolo/meinheld-gunicorn-flask).

The Docker image is built and published to Docker Hub as
`thomasgilgenast/private-ghp:latest` on every commit to main by GitHub Actions.

You can also build the image locally with

    docker build . -t private-ghp

And to run the image locally at http://localhost:5000

    docker run -d -p 5000:80 \
        -e FLASK_SECRET_KEY=... \
        -e PRIVATE_GHP_CLIENT_ID=... \
        -e PRIVATE_GHP_CLIENT_SECRET=... \
        private-ghp

Deploy
------

To deploy to gilgi cloud, use the following slack command:

    !cloud deploy ghp thomasgilgenast/private-ghp:latest

Note that for this to work we require the following env vars to be configured in
the gilgi cloud configuration for this subdomain:
 - `FLASK_SECRET_KEY`
 - `PRIVATE_GHP_CLIENT_ID`
 - `PRIVATE_GHP_CLIENT_SECRET`

After the first deploy, you may need to renew the SSL certs by running

    !cloud renew

Compiling dependencies
----------------------

    pip-compile --annotation-style=line
