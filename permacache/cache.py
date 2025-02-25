import os
import shutil
import sys
from functools import wraps
from pickle import UnpicklingError

from appdirs import user_cache_dir

from permacache.no_cache import no_cache_global
from permacache.out_file_cache import (
    add_file_cache_info,
    do_copy_files,
    process_out_file_parameter,
    split_out_files,
)

from .cache_miss_error import CacheMissError, error_on_miss, error_on_miss_global
from .dict_function import dict_function, parallel_output
from .hash import stringify
from .locked_shelf import IndividualFileLockedStore, LockedShelf
from .utils import bind_arguments

CACHE = user_cache_dir("permacache")


class CachedFunction:
    def __init__(
        self,
        function,
        key_function,
        path,
        *,
        parallel,
        shelf_type="combined-file",
        **kwargs,
    ):
        self.function = function
        self.key_function = key_function
        self.parallel = parallel
        if shelf_type == "combined-file":
            self.shelf = LockedShelf(path, **kwargs)
        elif shelf_type == "individual-file":
            self.shelf = IndividualFileLockedStore(path, **kwargs)
        else:
            raise ValueError(f"Unknown shelf type {shelf_type}")
        self._error_on_miss = False

    def _run_underlying(self, *args, **kwargs):
        if self._error_on_miss or error_on_miss_global.error_on_miss:
            raise CacheMissError
        return self.function(*args, **kwargs)

    def error_on_miss(self):
        return error_on_miss(self)

    def __call__(self, *args, **kwargs):
        if no_cache_global.no_cache:
            return self._run_underlying(*args, **kwargs)

        key = self.key_function(args, kwargs, parallel=self.parallel)
        if isinstance(key, parallel_output):
            return self.call_parallel(key.values, args, kwargs)

        key = stringify(key)

        with self.shelf as db:
            if key in db:
                try:
                    return db[key]
                except UnpicklingError as e:
                    # total hack. not sure why this is happening
                    print(f"Unpickling error: {e}", file=sys.stderr)
                    print(repr(key), file=sys.stderr)
                    print("Deleting key", file=sys.stderr)
                    del db[key]
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


class FileCachedFunction(CachedFunction):
    """
    Like CachedFunction, but with out files that store the actual contents
    """

    def __init__(self, *args, out_files, **kwargs):
        super().__init__(*args, **kwargs)
        self.out_files = out_files

    def __call__(self, *args, **kwargs):
        key_full = self.key_function(args, kwargs, parallel=self.parallel)
        key, out_files = split_out_files(key_full)
        assert not isinstance(
            key, parallel_output
        ), "should be impossible due to prior validation"

        key = stringify(key)

        with self.shelf as db:
            if key in db:
                result, file_cache_info = db[key]
                file_cache_info, success = do_copy_files(file_cache_info, out_files)
                if success:
                    return result
            else:
                file_cache_info = {}
        value = self._run_underlying(*args, **kwargs)
        file_cache_info = add_file_cache_info(file_cache_info, out_files)
        with self.shelf as db:
            db[key] = value, file_cache_info
        return value

    def cache_contains(self, *args, **kwargs):
        del args, kwargs
        raise NotImplementedError("not implemented for outfile cache")


def permacache(path, key_function=None, *, parallel=(), out_file=None, **kwargs):
    if key_function is None:
        key_function = dict()
    path = os.path.join(CACHE, path)

    if out_file is not None:
        out_file, key_function = process_out_file_parameter(
            key_function, parallel, out_file
        )

    def annotator(f):
        kf = key_function
        if isinstance(kf, dict):
            kf = dict_function(kf, f)
        if out_file is not None:
            return wraps(f)(
                FileCachedFunction(
                    f, kf, path, parallel=parallel, out_files=out_file, **kwargs
                )
            )
        return wraps(f)(CachedFunction(f, kf, path, parallel=parallel, **kwargs))

    return annotator


def to_file(path, zip_path):
    path = os.path.join(CACHE, path)
    shutil.make_archive(zip_path, "zip", path)


def from_file(path, zip_path):
    path = os.path.join(CACHE, path)
    if os.path.exists(path):
        raise RuntimeError(f"Cache already exists: {path}")
    shutil.unpack_archive(zip_path + ".zip", path, "zip")
