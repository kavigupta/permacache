import os

from appdirs import user_cache_dir

from .locked_shelf import LockedShelf
from .hash import stringify
from .dict_function import dict_function

CACHE = user_cache_dir("permacache")


class CachedFunction:
    def __init__(self, function, key_function, path):
        self.function = function
        self.key_function = key_function
        self.shelf = LockedShelf(path)

    def __call__(self, *args, **kwargs):
        key = stringify(self.key_function(*args, **kwargs))
        with self.shelf as db:
            if key in db:
                return db[key]
        value = self.function(*args, **kwargs)
        with self.shelf as db:
            # TODO maybe check if key is now in db
            db[key] = value
        return value


def permacache(path, key_function=lambda *args, **kwargs: [args, kwargs]):
    path = os.path.join(CACHE, path)

    def annotator(f):
        kf = key_function
        if isinstance(kf, dict):
            kf = dict_function(kf, f)
        return CachedFunction(f, kf, path)

    return annotator
