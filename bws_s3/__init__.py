from CTFd.plugins.bws_s3.uploader import BWSS3Uploader
from CTFd.utils.uploads import UPLOADERS


def load(app):
    UPLOADERS["bws"] = BWSS3Uploader
