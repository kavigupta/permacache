import json
import os
import shelve
import time
import uuid

from filelock import FileLock

from permacache.hash import stable_hash


class Lock:
    def __init__(self, lock_path, time_path):
        self.lock = FileLock(lock_path)
        self.time_path = time_path
        self.last_opened = float("-inf")
        self.unlocked = False

    def _get_last_modified(self):
        self._check()
        try:
            with open(self.time_path) as f:
                return float(f.read())
        # pylint: disable=broad-except
        except Exception:
            self.set_last_modified()
            return self._get_last_modified()

    def opened_after_last_modification(self):
        self._check()
        last_modified_time = self._get_last_modified()
        return self.last_opened >= last_modified_time

    def set_last_opened(self):
        self.last_opened = time.time()

    def set_last_modified(self):
        self._check()
        self.set_last_opened()
        with open(self.time_path, "w") as f:
            f.write(str(self.last_opened))

    def __enter__(self):
        self.lock.__enter__()
        self.unlocked = True
        return self

    def __exit__(self, *args, **kwargs):
        self.unlocked = False
        self.lock.__exit__(*args, **kwargs)

    def _check(self):
        assert self.unlocked, "can only perform this operation on an unlocked lock"


class LockedShelf:
    """
    A class that manages a shelf that can be accessed from multiple threads simultaneously.

    Mantains a cache of some of the elements of the dictionary. If it ever was not
        the most recent accessor of the shelf, the cache is entirely flushed.

    The cache is mantained over opening and closing of the shelf.
    """

    def __init__(
        self,
        path,
        multiprocess_safe=False,
        read_from_shelf_context_manager=None,
        allow_large_values=False,
    ):
        try:
            os.makedirs(path)
        except FileExistsError:
            pass
        self.path = path
        self.lock = Lock(self.path + "/lock", self.path + "/time")
        self.shelve_path = self.path + "/shelf"
        self.shelf = None
        self.cache = None
        self.multiprocess_safe = multiprocess_safe
        self.read_from_shelf_context_manager = read_from_shelf_context_manager
        self.allow_large_values = allow_large_values

    @property
    def shelf_kwargs(self):
        if self.allow_large_values:
            return {"protocol": 5}
        return {}

    def _update(self):
        if self.shelf is None:
            self.shelf = shelve.open(self.shelve_path, **self.shelf_kwargs)
            self.cache = {}
        else:
            assert self.cache is not None
            if not self.lock.opened_after_last_modification():
                self.cache = {}
                self.lock.set_last_opened()

    def _read_from_underlying_shelf(self, key):
        if self.read_from_shelf_context_manager is None:
            return self.shelf[key]
        with self.read_from_shelf_context_manager:
            return self.shelf[key]

    def __getitem__(self, key):
        self._update()

        if key not in self.cache:
            result = self.cache[key] = self._read_from_underlying_shelf(key)
            return result

        return self.cache[key]

    def __contains__(self, key):
        self._update()

        return key in self.cache or key in self.shelf

    def __setitem__(self, key, value):
        self._update()
        self.cache[key] = value
        self.shelf[key] = value
        self.lock.set_last_modified()

    def __delitem__(self, key):
        self._update()
        if key in self.cache:
            del self.cache[key]
        del self.shelf[key]
        self.lock.set_last_modified()

    def items(self):
        self._update()
        return list(self.shelf.items())

    def __enter__(self):
        self.lock.__enter__()
        return self

    def __exit__(self, *args, **kwargs):
        if self.multiprocess_safe:
            # for multi-processing safety, the only way is to close the shelf every time
            if self.shelf is not None:
                self.shelf.close()
            self.shelf = None
        self.lock.__exit__(*args, **kwargs)

    def close(self):
        if self.shelf is not None:
            self.shelf.close()


class IndividualFileLockedStore:
    """
    Like LockedShelf, but stores each key in a separate file. Should be
    broadly multiprocess safe, but you can enhance this by using the
    multiprocess_safe flag.
    """

    def __init__(
        self, path, read_from_shelf_context_manager=None, multiprocess_safe=False
    ):
        try:
            os.makedirs(path)
        except FileExistsError:
            pass
        self.path = path
        self.lock = Lock(self.path + "/lock", self.path + "/time")
        self.cache = None
        self.read_from_shelf_context_manager = read_from_shelf_context_manager
        self.multi_process_safe = multiprocess_safe

    def _path_for_key(self, key):
        if len(key) < 40 and all(c.isalnum() or c in "-_.,[](){} " for c in key):
            return os.path.join(self.path, "." + key)
        key = stable_hash(key)[:20]
        return os.path.join(self.path, key)

    def __getitem__(self, key):
        with open(self._path_for_key(key), "r") as f:
            result = json.load(f)
        return result[key]

    def __contains__(self, key):
        return os.path.exists(self._path_for_key(key))

    def __setitem__(self, key, value):
        temporary_path = self._path_for_key(key) + "." + uuid.uuid4().hex[:10]
        with open(temporary_path, "w") as f:
            json.dump({key: value}, f)
        os.rename(temporary_path, self._path_for_key(key))

    def __delitem__(self, key):
        os.remove(self._path_for_key(key))

    def items(self):
        for filename in os.listdir(self.path):
            with open(os.path.join(self.path, filename), "r") as f:
                yield json.load(f)

    def __enter__(self):
        if self.multi_process_safe:
            self.lock.__enter__()
        return self

    def __exit__(self, *args, **kwargs):
        if self.multi_process_safe:
            self.lock.__exit__(*args, **kwargs)

    def close(self):
        self.__exit__()
