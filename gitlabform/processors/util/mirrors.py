from urllib.parse import urlparse


def normalize_mirror_url_for_comparison(url: str) -> str:
    """Strip credentials from a mirror URL, so that a config URL with
    credentials matches the masked URL returned by GitLab
    (e.g. 'https://*****:*****@host/repo.git').
    """
    parsed = urlparse(url)
    clean_netloc = parsed.netloc.split("@")[-1]
    return parsed._replace(netloc=clean_netloc).geturl()


def mask_mirror_url_credentials(url: str) -> str:
    """Replace credentials in a mirror URL with the same masked form that
    GitLab returns, for displaying the URL without leaking secrets.
    """
    parsed = urlparse(url)
    if "@" not in parsed.netloc:
        return url
    host = parsed.netloc.split("@")[-1]
    return parsed._replace(netloc=f"*****:*****@{host}").geturl()
