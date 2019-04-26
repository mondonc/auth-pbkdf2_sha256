# auth-pbkdf2_sha256

pbkdf2 sha256 authentication service, designed to be used with Nginx.

Authenticate user against htpasswd file containing pbkdf2 sha256 hashes (typically a dump from Django auth_user table)

## Install

* Only need bottle. Install it via apt, pip, or simply download bootle.py file in same directory : 

```
wget https://raw.githubusercontent.com/bottlepy/bottle/release-0.12/bottle.py
```

* You have to create a secret file : 

```
echo `cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1` > secret.py
```

* The htpasswd file should be in same dir, containing :
```
$ cat ./htpasswd 
user1:pbkdf2_sha256$36000$n4WyxSTtxtEB$q1nmipGNCGrueWg50j+JJAlLpJE9XCSUORqWngZ25oU=
user2:pbkdf2_sha256$36000$CXjXiNAH76Jh$CVSqcZICqsjou5bhbigO5pJS/1eSXSr75DiVMc3MBSc=
...
```

Based on the Django auth_user table format: 
```
USERNAME : ALGO $ NB_ROUNDS $ SALT $ HASH
```

## Test

Run bottle webserver, listening on http://localhost:8123/auth

```
python auth-pbkdf2sha256.py
```



## Production (uwsgi)

### Dependancies

```
apt install uwsgi uwsgi-plugin-python nginx
```
(and also bottle of course)

### Uwsgi config

```
# cat /etc/uwsgi/apps-enabled/bottle.ini 
[uwsgi]
socket = /run/uwsgi/app/bottle/socket
chdir = /var/local/auth
master = true
plugins = python
file = auth-pbkdf2sha256.py
uid = www-data
gid = www-data
```

then `service uwsgi restart`

### Nginx config

```
$ cat /etc/nginx/sites-enabled/auth 

server {
    listen 127.0.0.1:8123;
    root /var/local/auth/;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/run/uwsgi/app/bottle/socket;
    }
}
```

then in your website nginx config : 

```
location = /login {
    proxy_pass              http://127.0.0.1:8123/login;
    proxy_set_header        X-Target  https://$host$request_uri;
}

location = /auth {
    internal;
    proxy_pass              http://127.0.0.1:8123;
    proxy_pass_request_body off;
    proxy_redirect off;
}

error_page 401 403 /login;

location / {
    auth_request     /auth;
    auth_request_set $auth_status $upstream_status;
    auth_request_set $remoteUser $upstream_http_REMOTE_USER;
    proxy_set_header REMOTE_USER $remoteUser;

    ...
    ...

}
```

Don't forget `service nginx restart`
