import os

from filelock import FileLock
import shelve
import time


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
        except:
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
        self, path, multiprocess_safe=False, read_from_shelf_context_manager=None
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

    def _update(self):
        if self.shelf is None:
            self.shelf = shelve.open(self.shelve_path)
            self.cache = {}
        else:
            assert self.cache is not None
            if not self.lock.opened_after_last_modification():
                self.cache = {}
                self.lock.set_last_opened()

    def _read_from_underlying_shelf(self, key):
        if self.read_from_shelf_context_manager is None:
            return self.shelf[key]
        else:
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
