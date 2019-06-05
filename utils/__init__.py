from constants import ATP_PREFIX

def resolve_url(url):
    if url and url != "#":
        return ATP_PREFIX + url

    return None
