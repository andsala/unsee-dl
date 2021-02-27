from urllib.parse import urlparse
from .unsee_new import DOMAIN as UNSEE_NEW_DOMAIN
from .unsee_old import UNSEE_OLD_DOMAIN


def get_album_id_from_url(album_url):
    """
    Extracts the album id from an url
    :param album_url: album url
    :return: album id
    """
    url = urlparse(album_url)
    if url.netloc in (UNSEE_OLD_DOMAIN,):  # old unsee is now "old.unsee.cc"
        return url.fragment
    elif url.netloc in ("", UNSEE_NEW_DOMAIN,):  # beta unsee is now: unsee.cc < removed empty ""
        return url.fragment
    return None


def is_old_album_id(album_id):
    return len(album_id) <= 8
