import os
from CTFd.models import db, Users
from CTFd.utils import get_config, set_config, get_app_config
from CTFd.utils.security.auth import login_user
from authlib.integrations.flask_client import OAuth
from flask import session, redirect, url_for


def load(app):
    def get_user(email):
        user = Users.query.filter_by(email=email).first()
        if user is not None:
            return user

    def create_user(email, name):
        user = Users(email=email, name=name.strip(), verified=True)
        db.session.add(user)
        db.session.commit()
        return user

    def get_or_create_user(email, name):
        user = get_user(email)
        if user is not None:
            return user
        return create_user(email, name)

    oauth = OAuth(app)
    oauth.register(
        "keycloak",
        client_id=get_app_config("KEYCLOAK_CLIENT_ID"),
        client_secret=get_app_config("KEYCLOAK_CLIENT_SECRET"),
        server_metadata_url=get_app_config("KEYCLOAK_METADATA_URL"),
        client_kwargs={
            "scope": "openid profile email",
            'code_challenge_method': 'S256'  # enable PKCE
        },
    )

    @app.route('/auth')
    def auth():
        token = oauth.keycloak.authorize_access_token()
        userinfo = token['userinfo']

        if userinfo:
            user = get_or_create_user(
                email=userinfo["email"],
                name=userinfo["name"])

            session.regenerate()
            login_user(user)
            db.session.close()

        return redirect('/')

    set_config('registration_visibility', False)
    app.view_functions['auth.login'] = lambda: oauth.keycloak.authorize_redirect(url_for('auth', _external=True))
    app.view_functions['auth.register'] = lambda: ('', 204)
    app.view_functions['auth.reset_password'] = lambda: ('', 204)
    app.view_functions['auth.confirm'] = lambda: ('', 204)
