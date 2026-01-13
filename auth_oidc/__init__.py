import os
from CTFd.models import db, Users, UserTokens
from CTFd.utils import get_config, set_config, get_app_config, user as current_user
from CTFd.utils.config import is_teams_mode
from CTFd.utils.helpers import get_errors, get_infos, markup
from CTFd.utils.security.auth import login_user, logout_user
from CTFd.utils.user import get_current_user, get_current_team
from authlib.integrations.flask_client import OAuth
from flask import session, redirect, render_template, url_for


def load(app):
    def settings():
        infos = get_infos()
        errors = get_errors()

        user = get_current_user()

        if is_teams_mode() and get_current_team() is None:
            team_url = url_for("teams.private")
            infos.append(
                markup(
                    f'In order to participate you must either <a href="{team_url}">join or create a team</a>.'
                )
            )

        tokens = UserTokens.query.filter_by(user_id=user.id).all()

        return render_template(
            "settings.html",
            name=user.name,
            email=user.email,
            language=user.language,
            website=user.website,
            affiliation=user.affiliation,
            country=user.country,
            tokens=tokens,
            prevent_name_change=True,
            infos=infos,
            errors=errors,
        )

    # The format used by the view_functions dictionary is blueprint.view_function_name
    app.view_functions['views.settings'] = settings

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
                name=userinfo["preferred_username"]
            )

            session.regenerate()
            login_user(user)
            session.permanent = False
            session["id_token"] = token["id_token"]

            db.session.close()

        return redirect(url_for("challenges.listing"))

    @app.route('/post-logout')
    def logout():
        logout_user()
        return redirect(url_for("views.static_html"))

    def sso_logout():
        if current_user.authed():
            metadata = oauth.keycloak.load_server_metadata()
            return redirect(metadata["end_session_endpoint"] + "?id_token_hint=" + session[
                "id_token"] + "&post_logout_redirect_uri=" + url_for("logout", _external=True))

        return redirect(url_for("views.static_html"))

    set_config('registration_visibility', False)
    app.view_functions['auth.login'] = lambda: oauth.keycloak.authorize_redirect(url_for('auth', _external=True))
    app.view_functions['auth.register'] = lambda: ('', 204)
    app.view_functions['auth.reset_password'] = lambda: ('', 204)
    app.view_functions['auth.confirm'] = lambda: ('', 204)
    app.view_functions['auth.logout'] = sso_logout
