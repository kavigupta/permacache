import os

import shutil

from appdirs import user_cache_dir

from .cache_miss_error import CacheMissError, error_on_miss, error_on_miss_global
from .locked_shelf import LockedShelf
from .hash import stringify
from .dict_function import dict_function, parallel_output
from .utils import bind_arguments

CACHE = user_cache_dir("permacache")


class CachedFunction:
    def __init__(self, function, key_function, path, *, parallel, **kwargs):
        self.function = function
        self.key_function = key_function
        self.parallel = parallel
        self.shelf = LockedShelf(path, **kwargs)
        self._error_on_miss = False

    def _run_underlying(self, *args, **kwargs):
        if self._error_on_miss or error_on_miss_global.error_on_miss:
            raise CacheMissError
        return self.function(*args, **kwargs)

    def error_on_miss(self):
        return error_on_miss(self)

    def __call__(self, *args, **kwargs):
        key = self.key_function(args, kwargs, parallel=self.parallel)
        if isinstance(key, parallel_output):
            return self.call_parallel(key.values, args, kwargs)

        key = stringify(key)

        with self.shelf as db:
            if key in db:
                return db[key]
        value = self._run_underlying(*args, **kwargs)
        with self.shelf as db:
            # TODO maybe check if key is now in db
            db[key] = value
        return value

    def cache_contains(self, *args, **kwargs):
        key = self.key_function(args, kwargs, parallel=self.parallel)
        assert not isinstance(key, parallel_output), "not supported"
        key = stringify(key)
        with self.shelf as db:
            return key in db

    def call_parallel(self, keys, args, kwargs):
        keys = [stringify(key) for key in keys]
        with self.shelf as db:
            keys_to_run = {k for k in set(keys) if k not in db}
        indices = []
        keys_for_indices = []
        for i, k in enumerate(keys):
            if k in keys_to_run:
                keys_to_run.remove(k)
                indices.append(i)
                keys_for_indices.append(k)
        assert not keys_to_run
        if not indices:
            values_for_indices = []
        else:
            arguments = bind_arguments(self.function, args, kwargs)
            arguments = arguments.copy()
            for k in self.parallel:
                arg = arguments[k]
                arg = [arg[i] for i in indices]
                arguments[k] = arg

            values_for_indices = self._run_underlying(**arguments)
        with self.shelf as db:
            for k, v in zip(keys_for_indices, values_for_indices):
                db[k] = v
            return [db[k] for k in keys]


def permacache(path, key_function=dict(), *, parallel=(), **kwargs):
    path = os.path.join(CACHE, path)

    def annotator(f):
        kf = key_function
        if isinstance(kf, dict):
            kf = dict_function(kf, f)
        return CachedFunction(f, kf, path, parallel=parallel, **kwargs)

    return annotator


def to_file(path, zip_path):
    path = os.path.join(CACHE, path)
    shutil.make_archive(zip_path, "zip", path)


def from_file(path, zip_path):
    path = os.path.join(CACHE, path)
    if os.path.exists(path):
        raise RuntimeError(f"Cache already exists: {path}")
    shutil.unpack_archive(zip_path + ".zip", path, "zip")
