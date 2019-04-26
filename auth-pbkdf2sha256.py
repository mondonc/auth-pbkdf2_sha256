#! /usr/bin/env python
# -*- coding: utf8 -*-

# Author: Clément Mondon clem@ent.sh

import bottle
import hashlib

from secret import SECRET

PASSWD_FILE = "./htpasswd"

app = application = bottle.Bottle()


@app.get('/auth')
def auth():
    """
    Asked by nginx, Check user's authentication.
    If not, redirect to login page
    """
    username = bottle.request.get_cookie("authuser", secret=SECRET)
    if username:
        bottle.response.set_header('REMOTE_USER', username)
        return "ok"
    else:
        bottle.abort(401, "Sorry, access denied.")


@app.get('/login')
def login():
    """
    Login form
    """
    target = bottle.request.query['target'].decode("base64") if "target" in bottle.request.query else bottle.request.get_header("X-Target")
    return """
    <html><head></head><body><center><form method="post" action="/login">
    <input name="username" type="text" placeholder="Utilisateur" /><br/>
    <input name="password" type="password" placeholder="Mot de passe"/><br/>
    <input type="submit" value="login"/>
    <input type="hidden" name="target" value="{}"/>
    </form></center></body></html>
    """.format(target)


@app.post('/login')
def login_post():
    """
    Authenticate user, redirect to target or login page
    """
    username = bottle.request.forms.get('username')
    password = bottle.request.forms.get('password')

    if not all((username, password)):
        bottle.abort(401, "Sorry, access denied.")

    if not check(username, password):
        bottle.redirect("/login?target={}".format(bottle.request.forms.get('target').encode("base64").strip()))

    bottle.response.set_header('REMOTE_USER', username)
    bottle.response.set_cookie("authuser", username, secret=SECRET, secure=True, max_age=604800)

    bottle.redirect(bottle.request.forms.get('target'))


def check(username, password):
    """
    Return True if username password verification successfull (pbkdf2/sha256)
    Even check password if user not exist to prevent user's existence leak
    """
    fuser, fpass = "", ""

    with open(PASSWD_FILE, 'r') as f:
        for line in f.readlines():
            fuser, fpass = line.split(':')
            if fuser == username:
                break

    algo, rounds, salt, phash = fpass.split('$')
    dk = hashlib.pbkdf2_hmac('sha256', password, salt, int(rounds))
    return phash.strip() == str(dk).encode("base64").strip()


if __name__ == '__main__':
    bottle.run(app, host='127.0.0.1', port=8123)
