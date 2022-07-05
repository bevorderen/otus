import hashlib
import json
import random

def get_score(store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    key_parts = [
        first_name or "",
        last_name or "",
        str(phone) or "",
        birthday if birthday is not None else "",
    ]
    key = "uid:" + hashlib.md5("".join(key_parts).encode("utf-8")).hexdigest()
    # try get from cache,
    # fallback to heavy calculation in case of cache miss
    score = store.cache_get(key) or 0
    score = float(score)
    if score:
        return score
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    # cache for 60 minutes
    store.cache_set(key, score, 60 * 60)
    return score


def set_interest(store, cid):
    interests = ["cars", "pets", "travel", "hi-tech", "sport", "music", "books", "tv", "cinema", "geek", "otus"]
    store.cache_set("i:%s" % cid, json.dumps(random.sample(interests, 2)), 60*60)

def get_interests(store, cid):
    r = store.get("i:%s" % cid)
    if not r:
        set_interest(store, cid)
    r = store.get("i:%s" % cid)
    return json.loads(r) if r else []
