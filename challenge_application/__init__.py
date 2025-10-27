import re
import requests
import time
import uuid
from CTFd.cache import cache
from CTFd.models import Challenges
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.plugins.dynamic_challenges import DynamicChallenge, DynamicValueChallenge
from CTFd.utils import get_app_config
from flask import request, session, Blueprint

redis = cache.cache._write_client
challenge_url_template = get_app_config("CHALLENGE_URL_TEMPLATE")


class DynamicChallengeWithApplication(DynamicChallenge):
    __mapper_args__ = {"polymorphic_identity": "with-application"}


class ChallengeWithApplication(DynamicValueChallenge):
    id = "with-application"  # Unique identifier used to register challenges
    name = "With application"  # Name of a challenge type
    templates = (
        {  # Handlebars templates used for each aspect of challenge editing & viewing
            "create": "/plugins/challenge_application/assets/create.html",
            "update": "/plugins/challenge_application/assets/update.html",
            "view": "/plugins/challenge_application/assets/view.html",
        }
    )
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/challenge_application/assets/create.js",
        "update": "/plugins/challenge_application/assets/update.js",
        "view": "/plugins/challenge_application/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/challenge_application/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "challenge_application",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = DynamicChallengeWithApplication


def get_challenge_url(challenge_id):
    if 'id' in session:
        user_id = session['id']
        hash = redis.get(f"challenge-{challenge_id}-{user_id}")

    return challenge_url_template.format(hash=hash.decode('utf-8')) if hash != None else None


def load(app):
    CHALLENGE_CLASSES["with-application"] = ChallengeWithApplication
    register_plugin_assets_directory(
        app, base_path="/plugins/challenge_application/assets/"
    )

    @app.route('/api/v1/plugins/challenge-application/start/<challenge_id>', methods=['POST'])
    def start_appplication(challenge_id):
        if 'id' in session:
            user_id = session['id']
            hash = uuid.uuid4().hex

            redis.set(f"challenge-{challenge_id}-{user_id}", hash, ex=3600)
            redis.zadd(f"applications-{challenge_id}", {hash: int(time.time())})

            return {"success": True, "url": get_challenge_url(challenge_id)}, 200
        else:
            return '', 403

    @app.route('/api/v1/plugins/challenge-application/status/<challenge_id>', methods=['GET'])
    def get_appplication_status(challenge_id):
        if 'id' in session:
            redis.zremrangebyscore(f"applications-{challenge_id}", 0, int(time.time()) - 4000)

            return {"success": True, "url": get_challenge_url(challenge_id)}, 200
        else:
            return '', 403

    @app.route('/api/v1/plugins/challenge-application/check/<challenge_id>', methods=['GET'])
    def check_appplication(challenge_id):
        if 'id' in session:
            try:
                requests.head(get_challenge_url(challenge_id), timeout=3.05)
                return {"success": True}, 200
            except requests.exceptions.RequestException:
                return {"success": False}, 500
        else:
            return '', 403

    @app.route('/api/v1/getparams.execute', methods=['POST'])
    def get_started_applications():
        request_data = request.get_json()
        challenge_id = request_data['input']['parameters']['challenge']

        current_time = int(time.time())
        hashes = redis.zrangebyscore(f"applications-{challenge_id}", current_time - 3600, current_time + 3600)

        return {'output': {'parameters': [{'hash': h.decode('utf-8')} for h in hashes]}}
